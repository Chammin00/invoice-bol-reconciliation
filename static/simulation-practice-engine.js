/**
 * Antigravity Interactive Packet Simulator & Gamified Audit Drill Engine (simulation-practice-engine.js)
 * 
 * Implements:
 * 1. Step-by-step B2B Document & Packet Journey Simulator synchronized with 3D NPR Topology
 * 2. Gamified Forensic Audit & System Design Drill Engine with smart fuzzy matching, hints,
 *    radial SVG progress ring, live streak counter, and Web Speech API audio narration.
 */

(function () {
  'use strict';

  const SCENARIOS = {
    freight_overcharge: {
      id: 'freight_overcharge',
      name: 'Scenario A: Carrier BOL $500 Math Overcharge (NorthStar Logistics)',
      badge: 'FLAGGED ANOMALY',
      badgeColor: '#f85149',
      steps: [
        {
          nodeIndex: 0,
          hop: 'HOP 01 / TLS INGESTION',
          srcDst: '198.51.100.42:443 -> 10.0.1.15:8000 (/api/documents/upload)',
          status: 'HTTP 200 STREAM_BUFFERED',
          log: '[INGEST] Received multipart PDF stream "NorthStar_Logistics_BOL-4091_MATH_ERROR.pdf" (48.2 KB, SHA-256: 9f8a..c41e). Persisted to /uploads.'
        },
        {
          nodeIndex: 1,
          hop: 'HOP 02 / AST REGEX PARSER',
          srcDst: 'DocumentParser.extract_text_from_pdf() -> _parse_text_payload()',
          status: 'CONFIDENCE 0.95',
          log: '[PARSER] Vendor="NorthStar Freight Logistics LLC" | Doc#="BOL-4091" | Extracted 3 line items: LTL Transit ($850.00), Fuel Surcharge ($119.00), Liftgate ($125.00).'
        },
        {
          nodeIndex: 2,
          hop: 'HOP 03 / DETERMINISTIC MATH ENGINE',
          srcDst: 'ReconciliationEngine.validate_document() -> Rule #3',
          status: 'ERROR: TAX_TOTAL_MISMATCH',
          log: '[INVARIANT VIOLATION] Line items sum to Subtotal $1,094.00 + Tax $0.00 = $1,094.00. Carrier stated Grand Total is $1,594.00. Discrepancy: +$500.00 overcharge caught!'
        },
        {
          nodeIndex: 3,
          hop: 'HOP 04 / HITL EXCEPTION QUEUE',
          srcDst: 'SQLite pipeline_records.db -> Status=FLAGGED',
          status: 'HUMAN CHECKPOINT REQUIRED',
          log: '[HITL] Auto-approval blocked. Record #2 routed to Flagged Discrepancy Queue with red callout badge for operator adjustment.'
        },
        {
          nodeIndex: 4,
          hop: 'HOP 05 / ERP LEDGER PROTECTION',
          srcDst: 'QuickBooks / Webhook Sink Gate',
          status: 'OVERBILLING PREVENTED ($500.00 SAVED)',
          log: '[LEDGER GUARD] Blocked $500.00 carrier billing error from entering accounts payable. Operator adjusts Grand Total to $1,094.00 and commits clean CSV.'
        }
      ]
    },
    hvac_clean: {
      id: 'hvac_clean',
      name: 'Scenario B: Clean HVAC Supplier Invoice Auto-Verification (Apex HVAC)',
      badge: 'AUTO-APPROVED',
      badgeColor: '#3fb950',
      steps: [
        {
          nodeIndex: 0,
          hop: 'HOP 01 / TLS INGESTION',
          srcDst: '203.0.113.88:443 -> 10.0.1.15:8000 (/api/documents/upload)',
          status: 'HTTP 200 STREAM_BUFFERED',
          log: '[INGEST] Received "Apex_HVAC_Supply_INV-8821.pdf" (39.6 KB). Assigned UTC ingestion timestamp.'
        },
        {
          nodeIndex: 1,
          hop: 'HOP 02 / AST REGEX PARSER',
          srcDst: 'DocumentParser._extract_line_items() -> 3 rows',
          status: 'CONFIDENCE 0.95',
          log: '[PARSER] Vendor="Apex HVAC Supply Co." | Doc#="INV-8821" | Items: 2x Compressor ($900), 4x R-410A ($720), 3x Copper Coil ($255).'
        },
        {
          nodeIndex: 2,
          hop: 'HOP 03 / DETERMINISTIC MATH ENGINE',
          srcDst: 'ReconciliationEngine.validate_document() -> All 6 Rules',
          status: '0 FLAGS (100% PASS)',
          log: '[MATH VERIFIED] Row extensions exact. Subtotal ($1,875.00) + Sales Tax ($150.00) == Grand Total ($2,025.00). Zero duplicates in SQLite index.'
        },
        {
          nodeIndex: 3,
          hop: 'HOP 04 / ZERO-TOUCH BYPASS',
          srcDst: 'AuditLog.action = AUTO_VERIFIED',
          status: 'STATUS = APPROVED',
          log: '[ZERO-TOUCH] Document satisfies all deterministic invariants and is < $5,000 threshold. Bypassed manual review (15 mins labor saved).'
        },
        {
          nodeIndex: 4,
          hop: 'HOP 05 / ERP CSV & WEBHOOK SYNC',
          srcDst: 'GET /api/export/csv -> QuickBooks Enterprise',
          status: 'EXPORTED (HTTP 200)',
          log: '[ERP COMMIT] Emitted 3 normalized GL line items to reconciled_export.csv and transitioned state to EXPORTED.'
        }
      ]
    },
    dental_high_value: {
      id: 'dental_high_value',
      name: 'Scenario C: High-Value Medical Equipment Gate >= $5,000 (Metro Dental)',
      badge: 'COMPLIANCE GATE',
      badgeColor: '#d29922',
      steps: [
        {
          nodeIndex: 0,
          hop: 'HOP 01 / TLS INGESTION',
          srcDst: '192.0.2.19:443 -> 10.0.1.15:8000 (/api/documents/upload)',
          status: 'HTTP 200 STREAM_BUFFERED',
          log: '[INGEST] Received "Metro_Dental_Supply_INV-9904_HIGH_VALUE.pdf" (51.0 KB).'
        },
        {
          nodeIndex: 1,
          hop: 'HOP 02 / AST REGEX PARSER',
          srcDst: 'DocumentParser._extract_totals()',
          status: 'CONFIDENCE 0.95',
          log: '[PARSER] Vendor="Metro Dental Lab & Equipment Inc." | Doc#="INV-9904" | Subtotal=$7,650.00, Tax=$612.00, Total=$8,262.00.'
        },
        {
          nodeIndex: 2,
          hop: 'HOP 03 / DETERMINISTIC MATH ENGINE',
          srcDst: 'ReconciliationEngine -> Rule #5 (High-Value Gate)',
          status: 'INFO: HIGH_VALUE_THRESHOLD',
          log: '[POLICY TRIGGER] Math is exact ($7,650 + $612 = $8,262), but Grand Total ($8,262.00) >= $5,000.00 executive sign-off policy.'
        },
        {
          nodeIndex: 3,
          hop: 'HOP 04 / EXECUTIVE SIGN-OFF CHECKPOINT',
          srcDst: 'Controller / Practice Admin Approval Queue',
          status: 'AWAITING 1-CLICK SIGN-OFF',
          log: '[HITL] Flagged with HIGH_VALUE_THRESHOLD badge. Practice Administrator verifies capital purchase and clicks Approve.'
        },
        {
          nodeIndex: 4,
          hop: 'HOP 05 / WEBHOOK DISPATCH',
          srcDst: 'POST /api/export/webhook -> NetSuite ERP',
          status: 'SYNCED (2 ITEMS)',
          log: '[ERP COMMIT] Dispatched signed JSON payload via httpx.AsyncClient to ERP endpoint with full audit trail.'
        }
      ]
    },
    row_extension_error: {
      id: 'row_extension_error',
      name: 'Scenario D: Contractor Row Multiplication Mismatch (Summit Property)',
      badge: 'ROW MATH ERROR',
      badgeColor: '#f85149',
      steps: [
        {
          nodeIndex: 0,
          hop: 'HOP 01 / TLS INGESTION',
          srcDst: '198.18.0.77:443 -> 10.0.1.15:8000 (/api/documents/upload)',
          status: 'HTTP 200 STREAM_BUFFERED',
          log: '[INGEST] Received contractor invoice "Summit_Property_Repair_INV-3318_ROW_ERROR.pdf".'
        },
        {
          nodeIndex: 1,
          hop: 'HOP 02 / AST REGEX PARSER',
          srcDst: 'DocumentParser._extract_line_items()',
          status: 'CONFIDENCE 0.95',
          log: '[PARSER] Extracted Line Item #1: "Roof Membrane Flashing Repair (Bldg B)" | Qty: 4 | Unit: $175.00 | Stated Row Total: $900.00.'
        },
        {
          nodeIndex: 2,
          hop: 'HOP 03 / DETERMINISTIC MATH ENGINE',
          srcDst: 'ReconciliationEngine -> Rule #3b (Row Extension)',
          status: 'ERROR: ROW_EXTENSION_MISMATCH',
          log: '[ROW MATH FAILURE] Item #1: 4.0 x $175.00 = $700.00 expected, but contractor billed $900.00 (+$200.00 row inflation)!'
        },
        {
          nodeIndex: 3,
          hop: 'HOP 04 / HITL LIVE RECALCULATION',
          srcDst: 'Split-View Line Item Editor -> recalcItemRow()',
          status: 'OPERATOR CORRECTED',
          log: '[HITL] Operator opens modal, clicks Save & Re-Check Rules, automatically recalculating row total to $700.00 and Subtotal to $1,000.00.'
        },
        {
          nodeIndex: 4,
          hop: 'HOP 05 / CLEAN LEDGER EXPORT',
          srcDst: 'GET /api/export/csv',
          status: 'RECONCILED & EXPORTED',
          log: '[ERP COMMIT] $200.00 line-item overcharge eliminated. Clean record exported to property management accounting.'
        }
      ]
    }
  };

  const DRILL_QUESTIONS = [
    {
      id: 'q1',
      title: '01. Line-Item vs. Subtotal Validation Code',
      prompt: 'When the sum of extracted line items ($1,094.00) does not equal the invoice stated subtotal ($1,594.00) beyond the $0.02 floating-point guard, what exact validation flag code does ReconciliationEngine emit?',
      acceptedAnswers: ['line_item_sum_mismatch', 'line item sum mismatch'],
      canonicalAnswer: 'LINE_ITEM_SUM_MISMATCH',
      hint: 'Check reconciliation_engine.py Rule #2: three words joined by underscores ending in _MISMATCH.',
      rationale: 'ReconciliationEngine Rule #2 computes round(sum(item.total_price), 2) and compares it against subtotal with a $0.02 tolerance, emitting ERROR code LINE_ITEM_SUM_MISMATCH when violated.'
    },
    {
      id: 'q2',
      title: '02. Subtotal + Tax vs. Grand Total Invariant',
      prompt: 'NorthStar Freight Logistics bills a Subtotal of $1,094.00 and Sales Tax of $0.00, but prints a Grand Total of $1,594.00 on BOL-4091. What is the exact dollar overcharge caught by TAX_TOTAL_MISMATCH?',
      acceptedAnswers: ['500', '$500', '500.00', '$500.00', '500 dollars'],
      canonicalAnswer: '$500.00',
      hint: 'Subtract the calculated total ($1,094.00 + $0.00) from the billed Grand Total ($1,594.00).',
      rationale: 'Calculated total is $1,094.00 + $0.00 = $1,094.00. The billed Grand Total is $1,594.00, resulting in an exact $500.00 vendor overbilling discrepancy caught in 0.2 seconds.'
    },
    {
      id: 'q3',
      title: '03. Executive Sign-Off Threshold Rule',
      prompt: 'At what minimum Grand Total dollar threshold does ReconciliationEngine automatically attach the HIGH_VALUE_THRESHOLD compliance flag for manager sign-off?',
      acceptedAnswers: ['5000', '$5000', '5,000', '$5,000', '5000.00', '$5,000.00'],
      canonicalAnswer: '$5,000.00',
      hint: 'Check Rule #5 in reconciliation_engine.py or the Metro Dental Supply invoice threshold.',
      rationale: 'Any transaction with total >= $5,000.00 triggers the HIGH_VALUE_THRESHOLD flag so high-value capital purchases require explicit managerial sign-off.'
    },
    {
      id: 'q4',
      title: '04. Composite Duplicate Detection Key',
      prompt: 'To prevent paying the same supplier bill twice, the SQLite duplicate check queries database.Document using vendor_name and what second column?',
      acceptedAnswers: ['document_number', 'document number', 'doc_num', 'invoice_number', 'invoice number'],
      canonicalAnswer: 'document_number',
      hint: 'It stores the extracted Invoice #, BOL #, or PO # on the Document ORM model.',
      rationale: 'Rule #4 queries database.Document filtering on both Document.vendor_name == vendor and Document.document_number == doc_num (excluding the current record ID on updates).'
    },
    {
      id: 'q5',
      title: '05. Outbound ERP Async HTTP Client',
      prompt: 'Which asynchronous Python HTTP client library is used in POST /api/export/webhook to dispatch reconciled JSON payloads with a 10.0-second timeout?',
      acceptedAnswers: ['httpx', 'httpx.asyncclient', 'asyncclient'],
      canonicalAnswer: 'httpx (httpx.AsyncClient)',
      hint: 'Check the top imports of main.py and line 384 inside export_webhook().',
      rationale: 'main.py uses async with httpx.AsyncClient(timeout=10.0) as client to perform non-blocking POST requests to external Zapier, Make, or ERP webhook endpoints.'
    },
    {
      id: 'q6',
      title: '06. Row Extension Arithmetic Check',
      prompt: 'On Summit Property invoice INV-3318, a contractor bills Qty 4 at Unit Price $175.00 but lists the row total as $900.00. What is the correct extended row total?',
      acceptedAnswers: ['700', '$700', '700.00', '$700.00'],
      canonicalAnswer: '$700.00',
      hint: 'Multiply Quantity (4) by Unit Price ($175.00).',
      rationale: '4 units * $175.00/unit = $700.00. Rule #3b (ROW_EXTENSION_MISMATCH) verifies qty * unit_price == total_price on every individual line item.'
    }
  ];

  const SimAndDrillEngine = {
    currentScenarioKey: 'freight_overcharge',
    currentStepIndex: -1,
    drillState: {},
    streak: 0,

    init: function () {
      DRILL_QUESTIONS.forEach(q => {
        this.drillState[q.id] = { solved: false, attempts: 0 };
      });
      this.renderDrillCards();
      this.updateDrillTelemetry();
      this.selectScenario('freight_overcharge');
    },

    selectScenario: function (key) {
      if (!SCENARIOS[key]) return;
      this.currentScenarioKey = key;
      this.currentStepIndex = -1;
      const sc = SCENARIOS[key];

      const nameEl = document.getElementById('sim-scenario-title');
      if (nameEl) nameEl.textContent = sc.name;

      const badgeEl = document.getElementById('sim-scenario-badge');
      if (badgeEl) {
        badgeEl.textContent = sc.badge;
        badgeEl.style.borderColor = sc.badgeColor;
        badgeEl.style.color = sc.badgeColor;
      }

      const stepCounter = document.getElementById('sim-step-counter');
      if (stepCounter) stepCounter.textContent = `Step 0 / ${sc.steps.length}`;

      const logStream = document.getElementById('sim-terminal-stream');
      if (logStream) {
        logStream.innerHTML = `<div class="text-slate-400 font-mono text-xs">[READY] Loaded ${sc.name}. Click "Run Next Hop Step" to trace packet & math execution across the 3D NPR pipeline.</div>`;
      }

      document.querySelectorAll('.scenario-select-btn').forEach(btn => {
        btn.classList.toggle('active-scenario-btn', btn.dataset.scenario === key);
      });

      if (window.NPR3DEngine) {
        window.NPR3DEngine.focusNode(0, false);
      }
    },

    stepNextHop: function () {
      const sc = SCENARIOS[this.currentScenarioKey];
      if (!sc) return;

      if (this.currentStepIndex + 1 >= sc.steps.length) {
        this.currentStepIndex = -1;
      }
      this.currentStepIndex++;

      const step = sc.steps[this.currentStepIndex];
      const stepCounter = document.getElementById('sim-step-counter');
      if (stepCounter) {
        stepCounter.textContent = `Step ${this.currentStepIndex + 1} / ${sc.steps.length}`;
      }

      if (window.NPR3DEngine) {
        window.NPR3DEngine.focusNode(step.nodeIndex, false);
      }

      const logStream = document.getElementById('sim-terminal-stream');
      if (logStream) {
        if (this.currentStepIndex === 0) logStream.innerHTML = '';
        const entry = document.createElement('div');
        const isErr = step.status.includes('ERROR') || step.status.includes('VIOLATION');
        const statusColor = isErr ? '#f85149' : (step.status.includes('PASS') || step.status.includes('EXPORTED') || step.status.includes('SAVED') ? '#3fb950' : '#58a6ff');

        entry.className = 'p-2.5 rounded border border-[#30363d] bg-[#090d16] font-mono text-xs space-y-1 mb-2';
        entry.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#dfba73]">${step.hop}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold" style="background:rgba(255,255,255,0.05); color:${statusColor}; border:1px solid ${statusColor}">${step.status}</span>
          </div>
          <div class="text-[11px] text-[#8b949e]">${step.srcDst}</div>
          <div class="text-white leading-relaxed">${step.log}</div>
        `;
        logStream.appendChild(entry);
        logStream.scrollTop = logStream.scrollHeight;
      }
    },

    resetScenario: function () {
      this.selectScenario(this.currentScenarioKey);
    },

    normalizeStr: function (s) {
      return (s || '').toString().toLowerCase().replace(/[^a-z0-9_.]/g, ' ').replace(/\s+/g, ' ').trim();
    },

    renderDrillCards: function () {
      const container = document.getElementById('drill-cards-grid');
      if (!container) return;
      container.innerHTML = '';

      DRILL_QUESTIONS.forEach(q => {
        const card = document.createElement('div');
        card.className = 'detail-card';
        card.id = `drill-card-${q.id}`;
        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="detail-heading">${q.title}</span>
            <span id="drill-badge-${q.id}" class="text-[11px] font-mono px-2 py-0.5 rounded border border-[#30363d] text-[#8b949e]">UNSOLVED</span>
          </div>
          <p class="text-xs text-[#e2e8f0] leading-relaxed">${q.prompt}</p>
          <div class="flex items-center gap-2 mt-1">
            <input type="text" id="drill-input-${q.id}" placeholder="Type exact technical answer..." 
              class="flex-1 bg-[#010409] border border-[#30363d] rounded px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-[#58a6ff]"
              onkeydown="if(event.key==='Enter') window.SimAndDrillEngine.checkAnswer('${q.id}')">
            <button onclick="window.SimAndDrillEngine.checkAnswer('${q.id}')" class="gh-btn-primary">Check</button>
          </div>
          <div class="flex items-center gap-2 pt-1">
            <button onclick="window.SimAndDrillEngine.showHint('${q.id}')" class="gh-btn text-xs">Hint</button>
            <button onclick="window.SimAndDrillEngine.revealAnswer('${q.id}')" class="gh-btn text-xs">Reveal</button>
            <button onclick="window.SimAndDrillEngine.speakRationale('${q.id}')" class="gh-btn text-xs ml-auto" title="Web Speech API Audio Explanation">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
              <span>Read Audio</span>
            </button>
          </div>
          <div id="drill-feedback-${q.id}" class="hidden text-xs p-2.5 rounded border mt-1 leading-relaxed"></div>
        `;
        container.appendChild(card);
      });
    },

    checkAnswer: function (qId) {
      const q = DRILL_QUESTIONS.find(item => item.id === qId);
      if (!q) return;
      const inputEl = document.getElementById(`drill-input-${qId}`);
      const fbEl = document.getElementById(`drill-feedback-${qId}`);
      const badgeEl = document.getElementById(`drill-badge-${qId}`);
      if (!inputEl || !fbEl || !badgeEl) return;

      const userVal = this.normalizeStr(inputEl.value);
      const rawTrim = (inputEl.value || '').trim().toLowerCase();
      this.drillState[qId].attempts++;

      const isMatch = q.acceptedAnswers.some(ans => {
        const normAns = this.normalizeStr(ans);
        return userVal === normAns || rawTrim === ans.toLowerCase() || (userVal.length >= 3 && userVal.includes(normAns));
      });

      fbEl.classList.remove('hidden');
      if (isMatch) {
        if (!this.drillState[qId].solved) {
          this.drillState[qId].solved = true;
          this.streak++;
        }
        fbEl.style.background = 'rgba(63, 185, 80, 0.12)';
        fbEl.style.borderColor = 'rgba(63, 185, 80, 0.4)';
        fbEl.style.color = '#3fb950';
        fbEl.innerHTML = `<strong>VERIFIED: ${q.canonicalAnswer}</strong><br/><span class="text-[#e2e8f0]">${q.rationale}</span>`;
        badgeEl.textContent = 'VERIFIED';
        badgeEl.style.color = '#3fb950';
        badgeEl.style.borderColor = '#3fb950';
      } else {
        this.streak = 0;
        fbEl.style.background = 'rgba(248, 81, 73, 0.12)';
        fbEl.style.borderColor = 'rgba(248, 81, 73, 0.4)';
        fbEl.style.color = '#f85149';
        fbEl.innerHTML = `<strong>MISMATCH:</strong> Try again or click Hint for architectural guidance.`;
      }
      this.updateDrillTelemetry();
    },

    showHint: function (qId) {
      const q = DRILL_QUESTIONS.find(item => item.id === qId);
      const fbEl = document.getElementById(`drill-feedback-${qId}`);
      if (!q || !fbEl) return;
      fbEl.classList.remove('hidden');
      fbEl.style.background = 'rgba(88, 166, 255, 0.12)';
      fbEl.style.borderColor = 'rgba(88, 166, 255, 0.4)';
      fbEl.style.color = '#58a6ff';
      fbEl.innerHTML = `<strong>ARCHITECTURAL HINT:</strong> <span class="text-[#e2e8f0]">${q.hint}</span>`;
    },

    revealAnswer: function (qId) {
      const q = DRILL_QUESTIONS.find(item => item.id === qId);
      const inputEl = document.getElementById(`drill-input-${qId}`);
      if (!q || !inputEl) return;
      inputEl.value = q.canonicalAnswer;
      this.checkAnswer(qId);
    },

    autoFillAll: function () {
      DRILL_QUESTIONS.forEach(q => this.revealAnswer(q.id));
    },

    resetAllDrills: function () {
      this.streak = 0;
      DRILL_QUESTIONS.forEach(q => {
        this.drillState[q.id] = { solved: false, attempts: 0 };
      });
      this.renderDrillCards();
      this.updateDrillTelemetry();
    },

    speakRationale: function (qId) {
      const q = DRILL_QUESTIONS.find(item => item.id === qId);
      if (!q || !('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(`${q.title}. Canonical solution: ${q.canonicalAnswer}. ${q.rationale}`);
      utterance.rate = 1.02;
      window.speechSynthesis.speak(utterance);
    },

    updateDrillTelemetry: function () {
      const total = DRILL_QUESTIONS.length;
      const solvedCount = Object.values(this.drillState).filter(s => s.solved).length;
      const pct = Math.round((solvedCount / total) * 100);

      const solvedEl = document.getElementById('drill-solved-count');
      if (solvedEl) solvedEl.textContent = `${solvedCount} / ${total}`;

      const pctEl = document.getElementById('drill-pct-label');
      if (pctEl) pctEl.textContent = `${pct}%`;

      const streakEl = document.getElementById('drill-streak-count');
      if (streakEl) streakEl.textContent = `${this.streak}`;

      const sidebarReadiness = document.getElementById('sidebar-readiness-pct');
      if (sidebarReadiness) sidebarReadiness.textContent = `${pct}%`;

      const sidebarBar = document.getElementById('sidebar-readiness-bar');
      if (sidebarBar) sidebarBar.style.width = `${pct}%`;

      const circle = document.getElementById('drill-progress-ring');
      if (circle) {
        const radius = 26;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (pct / 100) * circumference;
        circle.style.strokeDasharray = `${circumference}`;
        circle.style.strokeDashoffset = `${offset}`;
      }
    }
  };

  window.SimAndDrillEngine = SimAndDrillEngine;
})();
