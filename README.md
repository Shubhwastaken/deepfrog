# 🧠 Customs Brain

AI-powered multi-agent customs document processing system designed for automated verification and compliance.

## 📋 Problem Statement
Manual customs document verification is a slow, error-prone, and labor-intensive process. Clearing agents and customs officers must manually verify thousands of Invoices and Bills of Lading daily, cross-referencing values and checking for compliance issues. This bottleneck leads to shipment delays and high operational costs.

## 💡 The Solution
**Customs Brain** provides an autonomous multi-agent AI system that:
- **Processes PDF Documents**: Automatically extracts data from Invoices and Lading documents.
- **Cross-Verifies Data**: Uses AI agents to ensure consistency between different document types.
- **Semantic Classification**: Integrates Vector Databases (ChromaDB) for intelligent HS code classification and document retrieval.
- **Security Protocols**: Implements mandatory PII encryption (Fernet) and secure password hashing (PBKDF2/Bcrypt) to ensure data privacy and compliance.

## 🛠️ Tech Stack
- **Frontend**: Python Flask (SSR) with centralized logging.
- **Backend API**: FastAPI (REST architecture) for high-performance data processing.
- **Database**: PostgreSQL for structured data and ChromaDB for vector embeddings.
- **Cache & Queue**: Redis for task management and caching.
- **Security**: Fernet symmetric encryption and Bcrypt password hashing.
- **Infrastructure**: Docker & Docker Compose for seamless deployment.

## 🚀 How to Run

### 1. Prerequisites
- Docker & Docker Compose installed.
- Python 3.9+ (for local development).

### 2. Environment Setup
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Fill in your `SECRET_KEY`, `ENCRYPTION_KEY`, and LLM API keys.

### 3. Running with Docker
```bash
docker-compose up --build
```
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend Swagger API**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Local Development (Frontend)
```bash
cd frontend
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
python app.py
```

## 📸 Screenshots

### Login & Authentication
![Login Screen](https://via.placeholder.com/800x450.png?text=Login+Screen+coming+soon...)

### Dashboard & Document Processing
![Dashboard](https://via.placeholder.com/800x450.png?text=Dashboard+&+Results...)
---
Developed by **Ankit** for DeepFrog AI Solutions Pvt. Ltd.
