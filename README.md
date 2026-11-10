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

2. **Deterministic Business Rules Engine (6 Core Invariants)**:
   - **Row Extension Math (`ROW_EXTENSION_MISMATCH`)**: Verifies `Quantity × Unit Price == Row Total` on every line item.
   - **Line-Item Subtotal Verification (`LINE_ITEM_SUM_MISMATCH`)**: Sum of line items vs. stated Subtotal.
   - **Tax & Grand Total Verification (`TAX_TOTAL_MISMATCH` & `TAX_RATE_ANOMALY`)**: Verifies `Subtotal + Tax == Grand Total` and flags effective tax rates $> 15\%$.
   - **Duplicate Detection (`DUPLICATE_DOCUMENT`)**: Blocks already processed invoices for the same `Vendor + Document #`.
   - **High-Value Alerts (`HIGH_VALUE_THRESHOLD`)**: Automatically flags transactions $\ge$ \$5,000 for management sign-off.

3. **3D Non-Photorealistic (NPR) Pipeline Topology & Packet Simulator**:
   - Interactive Three.js WebGL 3D scene using custom cel/toon shaders, procedural hand-drawn cross-hatching textures, and inverted-hull ink silhouette outlines (zero sterile CGI plastic sheen).
   - Step-by-step packet and discrepancy simulator across 4 B2B operational scenarios with synchronized 3D node inspection and Web Speech API audio narration.

4. **Client Acquisition ROI & Statement of Work (SOW) Studio**:
   - Live financial calculator (`POST /api/roi/calculate`) and custom Markdown Statement of Work generator (`POST /api/proposal/generate`) to close \$2,500 setup + \$350/mo retainer deals on screen-share calls.

5. **Forensic Reconciliation Audit Drill Engine**:
   - Gamified 6-challenge architectural verification deck with smart fuzzy matching, hints, radial SVG mastery ring, and audio narration.

6. **Enterprise Fullscreen Layout ($100\text{vw} \times 100\text{vh}$) & ERP Sync**:
   - GitHub Primer matte dark console with collapsible left sidebar (`280px` to `64px`), `Ctrl+K` command search, and 3-way dockable architecture inspector (`Left`, `Center`, `Right`).
   - One-click batch approval (`POST /api/documents/batch-approve`), QuickBooks CSV export, and async outbound webhook dispatch (`POST /api/export/webhook`).

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
