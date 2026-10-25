# Antigravity Operations Engine: Ingestion & Reconciliation Pipeline

A production-grade, deterministic operations pipeline for B2B back-office document processing, discrepancy detection, and accounting data reconciliation.

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```
Open your browser and navigate to: **`http://127.0.0.1:8000`**

### 3. Generate Sample Data (Live Demo Mode)
Click the **"Load Live Sales Demo"** button on the top right of the dashboard, or run:
```bash
python generate_demo_data.py
```

---

## 🛠 Features

1. **Multi-Format Document Parsing**:
   - Ingests PDFs, CSVs, and plain text documents.
   - Extracts structured headers (Vendor, Invoice #, Date) and tabular line items.

2. **Deterministic Business Rules Engine**:
   - **Math Verification**: Sum of line items vs. Subtotal vs. Grand Total.
   - **Duplicate Detection**: Flags already processed invoices for the same vendor.
   - **High-Value Alerts**: Automatically flags transactions $\ge$ \$5,000 for management sign-off.

3. **Human-in-the-Loop (HITL) Dashboard**:
   - Real-time KPI counters (Labor Time Saved, Flagged Anomalies, Total Volume).
   - Side-by-side inspection view with live line-item editing and re-validation.
   - Instant 1-click batch approval.

4. **Export & ERP Sync**:
   - One-click CSV and JSON exports formatted for QuickBooks / Sage / ERPs.
   - Outbound webhook integration for automated Zapier or Make pipelines.

---

## 🧪 Running Automated Tests
```bash
pytest
```

---

## 📁 Project Structure

```
├── main.py                     # FastAPI application & REST endpoints
├── database.py                 # SQLite database & SQLAlchemy ORM models
├── schemas.py                  # Pydantic v2 data validation schemas
├── parser_engine.py            # Multi-format document text & table extraction
├── reconciliation_engine.py    # Deterministic math, duplicate, and risk rules
├── generate_demo_data.py       # Realistic mock PDF invoice generator
├── requirements.txt            # Python dependencies
├── CLIENT_PITCH_PLAYBOOK.md    # Complete sales pitch script, pricing & outreach
├── static/
│   └── index.html              # Modern responsive Tailwind CSS dashboard UI
└── tests/
    └── test_pipeline.py        # Automated test suite for validation & export
```
