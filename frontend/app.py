from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sys
import random
import logging
from cryptography.fernet import Fernet
import uuid
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import requests

load_dotenv(dotenv_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '.env'))

# ─── HACKINF PIPELINE IMPORT ──────────────────────────────────────────────────
HACKINF_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'hackinf')
sys.path.insert(0, HACKINF_DIR)

try:
    from extraction import extract_text
    from llm_extractor import process_documents
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    logging.warning(f"hackinf pipeline not available: {e}")
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_toasts_and_session'

# --- DATABASE CONFIGURATION ---
# Reads DATABASE_URL from .env  e.g. postgresql+asyncpg://postgres:pass@localhost:5432/customs_brain
_raw_url = os.environ.get('DATABASE_URL', '')
# Flask-SQLAlchemy (sync) needs plain postgresql://; async backends use postgresql+asyncpg://
_db_url = _raw_url.replace('postgresql+asyncpg://', 'postgresql://') \
                  .replace('mysql+aiomysql://', 'mysql+pymysql://') \
                  .replace('sqlite+aiosqlite:///', 'sqlite:///') \
                  .replace('sqlite+aiosqlite://', 'sqlite://')
if not _db_url:
    raise RuntimeError('DATABASE_URL is not set. Check your .env file.')
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

BACKEND_API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000')

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("customs_brain_frontend")

# --- MODELS ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(36), primary_key=True)
    email_obfuscated = db.Column(db.String(255), nullable=False)
    email_hash = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name_obfuscated = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- SECURITY UTILS ---
FERNET_KEY = b'zVIf8S9k4F-UaE_wBqC2hYV_XvF0Rk7aXFwR_tLpG3M='
fernet = Fernet(FERNET_KEY)

def encrypt_pii(data: str) -> str:
    if not data: return data
    return fernet.encrypt(data.encode()).decode()

def get_email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()

# --- APP CONFIG ---
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password")
        email_hash = get_email_hash(email)
        user = User.query.filter_by(email_hash=email_hash).first()
        if not user:
            flash("register", "error")
            return redirect(url_for("login"))
        if not check_password_hash(user.password_hash, password):
            flash("wrong password", "error")
            return redirect(url_for("login"))
        session['user_id'] = user.id
        session['user_email'] = email
        flash("Login successful", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    show_otp = False
    if request.method == "POST":
        action = request.form.get("action")
        if action == "register":
            email = request.form.get("email", "").lower().strip()
            name = request.form.get("name")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            if password != confirm_password:
                flash("password not same", "error")
                return render_template("register.html", show_otp=False, email=email, name=name)
            email_hash = get_email_hash(email)
            if User.query.filter_by(email_hash=email_hash).first():
                flash("User already exists", "error")
                return render_template("register.html", show_otp=False, email=email, name=name)
            otp = str(random.randint(1000, 9999))
            session['pending_registration'] = {"email": email, "name": name, "password": password, "otp": otp}
            show_otp = True
            return render_template("register.html", show_otp=True, email=email, name=name, demo_otp=otp)

        elif action == "verify_otp":
            user_otp = request.form.get("otp")
            pending = session.get('pending_registration')
            if not pending:
                flash("Session expired", "error")
                return redirect(url_for("register"))
            if user_otp != pending['otp']:
                flash("enter correct otp", "error")
                return render_template("register.html", show_otp=True, email=pending['email'], name=pending['name'], demo_otp=pending['otp'])
            try:
                new_user = User(
                    id=str(uuid.uuid4()),
                    email_obfuscated=encrypt_pii(pending['email']),
                    email_hash=get_email_hash(pending['email']),
                    password_hash=generate_password_hash(pending['password']),
                    name_obfuscated=encrypt_pii(pending['name'])
                )
                db.session.add(new_user)
                db.session.commit()
                session.pop('pending_registration', None)
                session['user_id'] = new_user.id
                session['user_email'] = pending['email']
                flash("Registration successful", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {e}")
                flash("An error occurred during registration", "error")
                return redirect(url_for("register"))
    return render_template("register.html", show_otp=show_otp)

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    # Check if we are tracking a job
    job_id = session.get('current_job_id')
    results = session.pop('analysis_results', None)
    
    # ── NOVEL FIX: Prevent Reload Loops ──────────────────────────────
    # If we have a job_id but no results, check the status once on load
    if job_id and not results:
        try:
            resp = requests.get(f"{BACKEND_API_URL}/status/{job_id}", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "completed":
                    results = data.get("result")
                    # Clear tracking ID so the tracking UI disappears and polling stops
                    session.pop('current_job_id', None)
                    logger.info(f"Job {job_id} is already completed. Loading results.")
        except Exception as e:
            logger.warning(f"Could not check status for {job_id}: {e}")
    # ──────────────────────────────────────────────────────────────────
    
    return render_template("dashboard.html", 
                         results=results, 
                         pipeline_available=PIPELINE_AVAILABLE,
                         current_job_id=session.get('current_job_id'))

@app.route("/api/status/<job_id>")
def get_status_proxy(job_id):
    """Proxy status requests to the FastAPI backend."""
    try:
        resp = requests.get(f"{BACKEND_API_URL}/status/{job_id}", timeout=5)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# ─── PROCESS ROUTE ────────────────────────────────────────────────────────────

@app.route("/process", methods=["POST"])
def process():
    if 'user_id' not in session:
        return redirect(url_for("login"))

    invoice_file = request.files.get('invoice')
    lading_file = request.files.get('lading')

    if not invoice_file or invoice_file.filename == '':
        flash("Please upload an Invoice PDF.", "error")
        return redirect(url_for("dashboard"))
    if not lading_file or lading_file.filename == '':
        flash("Please upload a Bill of Lading PDF.", "error")
        return redirect(url_for("dashboard"))

    try:
        # ── Step 1: Forward to FastAPI Queue System ──────────────────
        files = {
            'invoice': (invoice_file.filename, invoice_file.stream, invoice_file.content_type),
            'bol': (lading_file.filename, lading_file.stream, lading_file.content_type)
        }
        
        logger.info(f"Forwarding documents to Backend API at {BACKEND_API_URL}/process")
        resp = requests.post(f"{BACKEND_API_URL}/process", files=files, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"Backend API error: {resp.text}")
            flash("Failed to start analysis. Backend service might be down.", "error")
            return redirect(url_for("dashboard"))

        data = resp.json()
        job_id = data.get('job_id')
        
        # ── Step 2: Track Job ID in Session ──────────────────────────
        session['current_job_id'] = job_id
        flash("Analysis started — check progress below.", "success")
        
    except Exception as e:
        logger.error(f"Request error: {e}")
        flash("Could not connect to the Backend API.", "error")

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # use_reloader=False prevents subprocess spawn that breaks the OCR/LLM pipeline
    # threaded=True allows Flask to handle requests while the pipeline is processing
    app.run(debug=True, port=3000, use_reloader=False, threaded=True)
