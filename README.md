# Autonomous Document Processing and Compliance Agent 🚀

## 🎯 Problem Statement
International trade and customs clearance are currently plagued by manual, error-prone document verification. Customs officials and trade and logistics companies must manually verify **Invoices** and **Bills of Lading (BoL)**, assign complex **HS Codes**, and ensure compliance with varying country-specific regulations. This leads to delays, fines, and operational inefficiencies.

## 💡 Solution
Building an **Autonomous AI Agent** that handles the end-to-end customs compliance workflow. The system:
- **Extracts Data**: Pulls vessel details, item descriptions, and values from uploaded documents using OCR and NLP.
- **Compares Documents**: Automatically identifies mismatches between Invoices and Bills of Lading.
- **Classifies HS Codes**: Uses AI to predict the correct Harmonized System codes for items.
- **Validates Compliance**: Checks against regional trade rules and identifies potential issues.
- **Generates Declarations**: Outputs a structured, customs-compliant declaration (JSON/Table) ready for submission.

## 🛠️ Tech Stack
| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React (Vite), CSS3, Modern UI/UX Architecture |
| **Backend** | FastAPI (Python), REST API |
| **Async Processing** | Redis, Celery/Arq (Worker System) |
| **Database** | PostgreSQL |
| **AI/ML** | OCR Pipelines, LLM (for HS Classification & NLP) |
| **Infrastructure** | Docker, Single Docker-Compose Network |
| **Observability** | Structured Logging, Grafana (Planned) |

## 🏗️ Architecture & Workflow
The system observes a scalable, event-driven architecture:
1. **User Login**: Secure JWT-based authentication.
2. **File Upload**: Async upload of Invoice + BoL.
3. **Queueing**: Jobs are pushed to a **Redis Queue**.
4. **Worker Processing**: Minimum of 2 parallel workers pick up jobs.
   - **Extract**: Document parsing.
   - **Compare**: Document cross-validation.
   - **HS Predict**: AI-driven classification.
   - **Compliance**: Rule-based validation.
5. **Output**: Structured Customs Declaration generated and stored in DB.
6. **Dashboard**: Real-time polling for job status and results.

## 🚀 How to Run (Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- Node.js (for local frontend development)

### One-Command Setup
```bash
docker-compose up --build
```

### Manual Setup
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📸 Screenshots
*(To be added after implementation)*
- [ ] Login Page
- [ ] Document Upload Area
- [ ] Processing Jobs List
- [ ] Final Compliance Report & Declaration

## 🛡️ Security & Privacy
- **Encryption**: PII is encrypted at rest in the database.
- **Clean API**: PII is stripped from frontend-facing API results where not needed.
- **Role System**: Basic RBAC (User/Admin) implemented.

---
*Developed by DeepFrog AI Solutions for the Agentic AI & Intelligent Systems Hackathon.*
