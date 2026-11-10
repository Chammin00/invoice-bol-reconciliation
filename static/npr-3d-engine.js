/**
 * Antigravity 3D NPR Topology & Simulator Engine (npr-3d-engine.js)
 * 
 * Implements Non-Photorealistic Rendering (NPR) 3D models & interactive packet journey
 * simulation for B2B Document Ingestion, Math Reconciliation & ERP Ledger Sync.
 * 
 * Zero sterile CGI plastic sheen: Uses custom cel/toon shaders, procedural cross-hatching,
 * hand-drawn ink silhouette outlines (inverted hull), and warm paper-grain canvas textures.
 */

(function () {
  'use strict';

  const PIPELINE_NODES = [
    {
      id: 'inbound',
      label: '01. Inbound Ingestion Gateway',
      shortLabel: 'INGESTION',
      category: 'Multi-Format Stream Listener',
      pos: [-11.5, 0.8, 0],
      color: '#58a6ff',
      sketchColor: '#1f4e8c',
      shape: 'inbox_tray',
      role: 'Receives raw supplier PDFs, carrier Bills of Lading (BOL), EDI 210/810 streams, and CSV dispatch sheets via TLS 1.3 REST multipart endpoints.',
      specs: [
        ['Protocol', 'HTTPS POST /api/documents/upload'],
        ['Accepted MIME', 'application/pdf, text/csv, text/plain'],
        ['Max Payload', '50 MB per batch (Streaming Chunked)'],
        ['Throughput SLA', '< 45ms I/O buffer write']
      ],
      failureRecovery: 'Malformed binary streams or encrypted PDFs are quarantined to dead-letter storage and flagged for operator password entry.'
    },
    {
      id: 'parser',
      label: '02. OCR & Regex AST Parser',
      shortLabel: 'AST PARSER',
      category: 'Deterministic Extraction Layer',
      pos: [-5.8, -0.6, 1.2],
      color: '#bc8cff',
      sketchColor: '#59368a',
      shape: 'scanner_prism',
      role: 'Extracts structured header entities (Vendor, Invoice #, Date) and tabular line items (Description, Qty, Unit Price, Extended Total) using multi-pass regex grammars.',
      specs: [
        ['PDF Engine', 'pypdf Layout Stream + Multi-Line Cell Stitcher'],
        ['Header Patterns', 'Vendor / Inv # / BOL # / ISO-8601 Dates'],
        ['Confidence Floor', '0.75 (Auto-routes < 0.95 to HITL Queue)'],
        ['Latency', '80ms average per 3-page invoice']
      ],
      failureRecovery: 'When vendor table layouts shift, multi-line cell fallback triggers and highlights low-confidence fields in the split-screen inspector.'
    },
    {
      id: 'rules',
      label: '03. Math & Duplicate Rules Engine',
      shortLabel: 'MATH ENGINE',
      category: 'Zero-Hallucination Verification',
      pos: [0, 0.9, -0.5],
      color: '#f0883e',
      sketchColor: '#8a4412',
      shape: 'balance_octahedron',
      role: 'Executes 6 deterministic accounting invariants: row extension math (Qty * Unit == Row Total), Subtotal sum, Tax rate ceiling (<= 15%), Grand Total reconciliation, SQLite composite duplicate lookup, and $5,000+ high-value threshold.',
      specs: [
        ['Math Tolerance', '+/- $0.02 IEEE-754 rounding guard'],
        ['Duplicate Index', 'UNIQUE(vendor_name, document_number)'],
        ['High-Value Gate', '>= $5,000.00 Manager Sign-Off'],
        ['Execution Time', '< 4ms deterministic Python evaluation']
      ],
      failureRecovery: 'Any ERROR flag (e.g. $500 freight overcharge or row math mismatch) blocks auto-approval and routes immediately to the Flagged Anomaly Queue.'
    },
    {
      id: 'hitl',
      label: '04. HITL Exception Checkpoint',
      shortLabel: 'HITL QUEUE',
      category: 'Human-in-the-Loop Audit Workstation',
      pos: [5.8, -0.7, 1.0],
      color: '#d29922',
      sketchColor: '#73500a',
      shape: 'anvil_shield',
      role: 'Side-by-side operator inspection console comparing raw extracted text against editable line-item tables with live rule re-evaluation and 1-click batch approval.',
      specs: [
        ['Operator SLA', '5.2 seconds average exception review'],
        ['Audit Trail', 'Immutable UTC timestamped AuditLog rows'],
        ['Batch Action', 'POST /api/documents/batch-approve'],
        ['Labor Savings', '15.0 mins saved per processed document']
      ],
      failureRecovery: 'Full optimistic locking and audit rollback history preserve original raw text alongside human overrides.'
    },
    {
      id: 'erp',
      label: '05. ERP & Webhook Ledger Sink',
      shortLabel: 'ERP LEDGER',
      category: 'QuickBooks / Sage / NetSuite Sync',
      pos: [11.5, 0.6, 0],
      color: '#3fb950',
      sketchColor: '#196127',
      shape: 'ledger_vault',
      role: 'Transforms approved records into ERP-ready double-entry CSV batches or dispatches signed JSON payloads to outbound Zapier/Make/QuickBooks webhooks.',
      specs: [
        ['Export Formats', 'RFC-4180 CSV & Signed JSON Webhook'],
        ['Webhook Client', 'httpx.AsyncClient (10.0s timeout)'],
        ['State Transition', 'APPROVED -> EXPORTED + Audit Stamp'],
        ['Data Isolation', '100% Single-Tenant SQLite / Postgres']
      ],
      failureRecovery: 'If an outbound ERP webhook returns non-2xx or times out, status logs FAILED_OUTBOUND_CALL and queues the batch for deterministic retry.'
    }
  ];

  // Create hand-drawn cross-hatch & paper grain texture procedurally on a 2D canvas
  function createHandDrawnHatchTexture(baseHex, strokeHex) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');

    // Warm paper/gouache wash background
    ctx.fillStyle = baseHex;
    ctx.fillRect(0, 0, 256, 256);

    // Subtle organic watercolor stipple / grain
    for (let i = 0; i < 1200; i++) {
      const x = Math.random() * 256;
      const y = Math.random() * 256;
      const r = Math.random() * 1.8;
      ctx.fillStyle = i % 2 === 0 ? 'rgba(255,250,240,0.06)' : 'rgba(10,14,22,0.12)';
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Hand-drawn ink cross-hatching lines
    ctx.strokeStyle = strokeHex;
    ctx.lineWidth = 1.4;
    ctx.globalAlpha = 0.38;

    // Primary diagonal hatch
    for (let offset = -256; offset < 512; offset += 14) {
      ctx.beginPath();
      const jitter1 = (Math.random() - 0.5) * 3;
      const jitter2 = (Math.random() - 0.5) * 3;
      ctx.moveTo(offset + jitter1, 0);
      ctx.lineTo(offset + 256 + jitter2, 256);
      ctx.stroke();
    }

    // Secondary contour hatch
    ctx.globalAlpha = 0.2;
    for (let y = 8; y < 256; y += 22) {
      ctx.beginPath();
      ctx.moveTo(0, y + (Math.random() - 0.5) * 2);
      ctx.bezierCurveTo(85, y - 3, 170, y + 3, 256, y);
      ctx.stroke();
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    return texture;
  }

  // Create 3-tone discrete gradient map for Three.js MeshToonMaterial
  function createToonGradientMap() {
    const canvas = document.createElement('canvas');
    canvas.width = 4;
    canvas.height = 1;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#384252';
    ctx.fillRect(0, 0, 1, 1);
    ctx.fillStyle = '#7c889b';
    ctx.fillRect(1, 0, 1, 1);
    ctx.fillStyle = '#c8d1dc';
    ctx.fillRect(2, 0, 1, 1);
    ctx.fillStyle = '#fff8eb';
    ctx.fillRect(3, 0, 1, 1);

    const gradientMap = new THREE.CanvasTexture(canvas);
    gradientMap.minFilter = THREE.NearestFilter;
    gradientMap.magFilter = THREE.NearestFilter;
    gradientMap.generateMipmaps = false;
    return gradientMap;
  }

  // Add hand-inked silhouette outline + sketch wireframe to any geometry
  function buildNPRMeshGroup(geometry, baseColor, sketchColor, gradientMap) {
    const group = new THREE.Group();

    const hatchTex = createHandDrawnHatchTexture(baseColor, sketchColor);
    const toonMat = new THREE.MeshToonMaterial({
      color: 0xffffff,
      map: hatchTex,
      gradientMap: gradientMap
    });

    const mainMesh = new THREE.Mesh(geometry, toonMat);
    group.add(mainMesh);

    // Inverted Hull Ink Outline (classic NPR cel-shaded black ink contour)
    const outlineMat = new THREE.MeshBasicMaterial({
      color: 0x050811,
      side: THREE.BackSide
    });
    const outlineMesh = new THREE.Mesh(geometry, outlineMat);
    outlineMesh.scale.multiplyScalar(1.07);
    group.add(outlineMesh);

    // Expressive drafting ink edge lines
    const edgesGeo = new THREE.EdgesGeometry(geometry, 18);
    const edgesMat = new THREE.LineBasicMaterial({
      color: 0xfef3c7,
      transparent: true,
      opacity: 0.55
    });
    const edgesLine = new THREE.LineSegments(edgesGeo, edgesMat);
    edgesLine.scale.multiplyScalar(1.015);
    group.add(edgesLine);

    return { group, mainMesh, outlineMesh, edgesLine };
  }

  const NPR3DEngine = {
    scene: null,
    camera: null,
    renderer: null,
    nodeMeshes: [],
    packetMesh: null,
    activeNodeIndex: -1,
    wireframeMode: false,
    autoRotate: true,
    raycaster: null,
    mouse: null,
    isInitialized: false,

    init: function (containerId) {
      const container = document.getElementById(containerId);
      if (!container || typeof THREE === 'undefined') return;
      if (this.isInitialized) {
        this.handleResize(container);
        return;
      }

      const width = container.clientWidth || 900;
      const height = container.clientHeight || 430;

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 200);
      this.camera.position.set(0, 6.2, 23.5);
      this.camera.lookAt(0, 0, 0);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.innerHTML = '';
      container.appendChild(this.renderer.domElement);

      // Warm studio illustration lighting (zero specular plastic glare)
      const ambientLight = new THREE.AmbientLight(0xfaf0dc, 0.75);
      this.scene.add(ambientLight);

      const dirLight = new THREE.DirectionalLight(0xfffbeb, 1.1);
      dirLight.position.set(12, 22, 16);
      this.scene.add(dirLight);

      const backLight = new THREE.DirectionalLight(0x58a6ff, 0.45);
      backLight.position.set(-14, -10, -10);
      this.scene.add(backLight);

      // Architectural drafting blueprint grid floor
      const gridHelper = new THREE.GridHelper(34, 34, 0x30363d, 0x161b22);
      gridHelper.position.y = -3.4;
      this.scene.add(gridHelper);

      const gradientMap = createToonGradientMap();

      // Build each of the 5 pipeline stage 3D NPR sculptures
      this.nodeMeshes = [];
      PIPELINE_NODES.forEach((node, idx) => {
        let geo;
        if (node.shape === 'inbox_tray') {
          geo = new THREE.BoxGeometry(2.5, 1.9, 2.1);
        } else if (node.shape === 'scanner_prism') {
          geo = new THREE.CylinderGeometry(1.35, 1.55, 2.3, 6);
        } else if (node.shape === 'balance_octahedron') {
          geo = new THREE.OctahedronGeometry(1.75, 0);
        } else if (node.shape === 'anvil_shield') {
          geo = new THREE.DodecahedronGeometry(1.55, 0);
        } else {
          geo = new THREE.BoxGeometry(2.3, 2.5, 2.3);
        }

        const built = buildNPRMeshGroup(geo, node.color, node.sketchColor, gradientMap);
        built.group.position.set(node.pos[0], node.pos[1], node.pos[2]);
        built.group.userData = { nodeIndex: idx, nodeData: node };

        // Add orbital ink ring around each node
        const ringGeo = new THREE.TorusGeometry(2.15, 0.045, 8, 40);
        const ringMat = new THREE.MeshBasicMaterial({
          color: new THREE.Color(node.color),
          transparent: true,
          opacity: 0.45
        });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.rotation.x = Math.PI / 2.3;
        built.group.add(ringMesh);

        this.scene.add(built.group);
        this.nodeMeshes.push({
          ...built,
          ringMesh,
          baseY: node.pos[1],
          nodeData: node
        });
      });

      // Build hand-sketched spline conduits connecting nodes 0 -> 1 -> 2 -> 3 -> 4
      for (let i = 0; i < PIPELINE_NODES.length - 1; i++) {
        const start = new THREE.Vector3(...PIPELINE_NODES[i].pos);
        const end = new THREE.Vector3(...PIPELINE_NODES[i + 1].pos);
        const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
        mid.y += (i % 2 === 0 ? 1.4 : -1.2);

        const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
        const tubeGeo = new THREE.TubeGeometry(curve, 28, 0.09, 6, false);
        const tubeMat = new THREE.MeshBasicMaterial({
          color: 0x485263,
          transparent: true,
          opacity: 0.65
        });
        const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
        this.scene.add(tubeMesh);
      }

      // Create animated 3D Document Packet Courier (Origami/Parcel Cube)
      const pktGeo = new THREE.OctahedronGeometry(0.62, 0);
      const pktBuilt = buildNPRMeshGroup(pktGeo, '#dfba73', '#785616', gradientMap);
      pktBuilt.group.position.set(...PIPELINE_NODES[0].pos);
      this.scene.add(pktBuilt.group);
      this.packetMesh = pktBuilt.group;

      // Setup mouse picking & drag rotation
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
      let isDragging = false;
      let prevX = 0;

      const domElem = this.renderer.domElement;
      domElem.addEventListener('mousedown', (e) => {
        isDragging = true;
        prevX = e.clientX;
      });

      window.addEventListener('mouseup', () => {
        isDragging = false;
      });

      domElem.addEventListener('mousemove', (e) => {
        if (isDragging) {
          const deltaX = e.clientX - prevX;
          prevX = e.clientX;
          this.scene.rotation.y += deltaX * 0.005;
        }
      });

      domElem.addEventListener('click', (e) => {
        const rect = domElem.getBoundingClientRect();
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        this.raycaster.setFromCamera(this.mouse, this.camera);

        const targets = this.nodeMeshes.map(n => n.mainMesh);
        const intersects = this.raycaster.intersectObjects(targets, false);
        if (intersects.length > 0) {
          const hitGroup = intersects[0].object.parent;
          if (hitGroup && hitGroup.userData && typeof hitGroup.userData.nodeIndex === 'number') {
            this.focusNode(hitGroup.userData.nodeIndex, true);
          }
        }
      });

      window.addEventListener('resize', () => this.handleResize(container));
      this.isInitialized = true;
      this.animate();
    },

    handleResize: function (container) {
      if (!this.renderer || !this.camera || !container) return;
      const w = container.clientWidth || 900;
      const h = container.clientHeight || 430;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    },

    toggleWireframe: function () {
      this.wireframeMode = !this.wireframeMode;
      this.nodeMeshes.forEach(n => {
        n.mainMesh.material.wireframe = this.wireframeMode;
      });
      return this.wireframeMode;
    },

    resetCamera: function () {
      if (!this.scene || !this.camera) return;
      this.scene.rotation.set(0, 0, 0);
      this.camera.position.set(0, 6.2, 23.5);
      this.camera.lookAt(0, 0, 0);
    },

    focusNode: function (index, openInspectorFlag) {
      if (index < 0 || index >= PIPELINE_NODES.length) return;
      this.activeNodeIndex = index;
      const node = PIPELINE_NODES[index];

      // Move 3D packet courier to active node
      if (this.packetMesh) {
        this.packetMesh.position.set(node.pos[0], node.pos[1] + 2.3, node.pos[2]);
      }

      // Highlight active 3D node & update DOM pill cards
      this.nodeMeshes.forEach((n, idx) => {
        const isTarget = idx === index;
        n.group.scale.setScalar(isTarget ? 1.28 : 1.0);
        n.ringMesh.material.opacity = isTarget ? 0.95 : 0.35;
        n.outlineMesh.material.color.setHex(isTarget ? 0xf0883e : 0x050811);
      });

      document.querySelectorAll('.stage-node-pill').forEach((el, idx) => {
        el.classList.toggle('active-stage-node', idx === index);
      });

      if (openInspectorFlag && window.AntigravityEnterprise) {
        window.AntigravityEnterprise.openInspector({
          title: node.label,
          category: node.category,
          role: node.role,
          specs: node.specs,
          failureRecovery: node.failureRecovery
        });
      }
    },

    animate: function () {
      requestAnimationFrame(() => this.animate());
      const t = performance.now() * 0.001;

      this.nodeMeshes.forEach((n, idx) => {
        n.group.rotation.y = t * 0.45 + idx * 0.7;
        n.group.rotation.x = Math.sin(t * 0.8 + idx) * 0.15;
        n.group.position.y = n.baseY + Math.sin(t * 1.6 + idx * 1.1) * 0.18;
      });

      if (this.packetMesh) {
        this.packetMesh.rotation.y = -t * 2.2;
        this.packetMesh.rotation.z = t * 1.4;
      }

      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    },

    getNodes: function () {
      return PIPELINE_NODES;
    }
  };

  window.NPR3DEngine = NPR3DEngine;
})();
