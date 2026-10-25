# Client Acquisition & Sales Pitch Playbook
## "Operations & Document Reconciliation Workflow" Service

This playbook details how to sell this exact proof-of-concept pipeline to high-volume, low-tech businesses for **\$1,500 – \$3,000 upfront setup + \$250 – \$500/month recurring maintenance**.

---

## 1. Target Niches (Highest Conversion)

| Industry | Daily Pain Point | Key Buyer Title |
| :--- | :--- | :--- |
| **HVAC / Plumbing / Electrical Trades** | Dispatchers spend 3 hours/day matching supplier part receipts with job work orders | Operations Director, Owner |
| **Regional Freight / 3PL Logistics** | Discrepancies in carrier Bills of Lading, accessorial charges, and fuel surcharges | Freight Broker, Logistics Lead |
| **Dental & Medical Clinics** | Reconciling third-party lab bills against patient records | Practice Administrator, Office Manager |
| **Property Management** | Contractor repair invoices, multiple properties, utility bill routing | Property Ops Lead, Controller |

---

## 2. The Winning Pitch Angle

> **Golden Rule**: Never pitch "Autonomous AI Agents" or "LLM Chains". Low-tech business owners don't care about AI; they care about saving payroll hours and eliminating vendor overbilling.

### Cold Outreach / Inmail Template
> **Subject**: Eliminating manual invoice/dispatch entry for [Company Name]
>
> Hi [First Name],
>
> Most [HVAC / logistics / property] operators I speak with have their staff losing 12–15 hours every week manually cross-referencing vendor invoices, work orders, and accounting sheets.
>
> We built a deterministic reconciliation system that ingests your inbound supplier documents, automatically runs math and line-item checks against your database, flags overbilling, and pushes clean records straight to QuickBooks/CSV in seconds.
>
> If I show you a 3-minute live demo on your actual document formats, would you be open to a quick chat this Thursday?
>
> Best,  
> [Your Name]

---

## 3. The 3-Minute Live Sales Demo Script

When you get a prospect on a screen-share:

1. **Step 1: The Setup (0:00 – 0:45)**
   - Open the dashboard UI at `http://127.0.0.1:8000`.
   - *"Let me show you how our operations engine handles inbound invoices and catches billing errors before they hit your bank account."*
2. **Step 2: Drop the Document (0:45 – 1:30)**
   - Click **"Load Live Sales Demo"** or drop in a sample supplier invoice.
   - Show how in 0.2 seconds it extracts the vendor, invoice #, line items, and totals.
3. **Step 3: Show the Discrepancy Flag (1:30 – 2:15)**
   - Click **"Inspect"** on the flagged `NorthStar Logistics` document.
   - Point out the red callout: *"Look here—the vendor billed $1,594.00, but the line items only total $1,094.00. That’s a \$500 vendor overcharge that a tired employee on Friday at 4 PM would have approved. The engine flagged it instantly."*
4. **Step 4: The 1-Click Export (2:15 – 3:00)**
   - Click **"Approve & Validate"**, then click **"Export Reconciled CSV"** or show outbound webhook sync.
   - *"Your accounting team never has to re-type another line item. They just review discrepancies and export."*

---

## 4. Packaging & Pricing Architecture

### Package A: "Turnkey Operations Automator"
- **Setup Fee**: \$2,500 (one-time)
  - Custom schema adaptation for their 3 primary document formats (e.g. supply invoices, delivery tickets, timesheets).
  - Webhook or CSV export integration into QuickBooks / ERP / Google Sheets.
  - Staff onboarding walkthrough.
- **Monthly Retainer**: \$350 / month
  - Server hosting & database management.
  - Continuous rule updates when suppliers change invoice templates.
  - Email & phone monitoring support.

### ROI Math to Close the Deal:
- Average manual entry cost: 15 hours/week $\times$ \$22/hr employee = **\$1,430/month in wasted labor**.
- Your cost: **\$350/month**.
- **Net client savings: ~\$1,080/month + zero costly vendor overbilling errors.**

---

## 5. Objection Handling Cheat Sheet

- **"Is our financial data safe?"**  
  *Yes. Unlike public AI tools, this runs on an isolated dedicated database with strict deterministic checks. No raw client data is trained on public models.*

- **"What if a vendor changes their invoice format?"**  
  *The system includes a Human-in-the-Loop review queue. Any unknown field is flagged for a 5-second human review, and your monthly retainer covers updating the parser rules within 24 hours.*
