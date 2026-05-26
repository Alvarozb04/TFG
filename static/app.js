// =====================================================================
// GLOBAL VARIABLES & APPLICATION STATES
// =====================================================================
let currentTab = "vqc-tab";
let vqcLossChart = null;
let eventSource = null;
let currentDatasetData = [];

// =====================================================================
// INITIALIZATION ON DOM LOAD
// =====================================================================
document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    initVQCChart();
    loadInitialDataset();
    drawInitialCircuit();
    
    // Listen for configuration changes to update the circuit diagram dynamically
    document.getElementById("vqc-qubits").addEventListener("change", drawInitialCircuit);
    document.getElementById("vqc-layers").addEventListener("change", drawInitialCircuit);
    document.getElementById("vqc-ansatz").addEventListener("change", drawInitialCircuit);
    document.getElementById("vqc-embedding").addEventListener("change", drawInitialCircuit);
    document.getElementById("vqc-dataset").addEventListener("change", loadInitialDataset);
});

// =====================================================================
// 1. TAB NAVIGATION CONTROLLER
// =====================================================================
function initTabNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabs = document.querySelectorAll(".tab-content");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            tabs.forEach(t => t.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
            currentTab = targetTab;
            
            // Trigger specific redraws/actions based on the active tab
            if (targetTab === "qsvm-tab") {
                // If QSVM tab is selected, render a default blank matrix
                drawEmptyQSVMHeatmap();
                drawEmptyQSVMBoundaries();
            }
        });
    });
}

// =====================================================================
// 2. CHART.JS INITIALIZER (VQC & COMPARISON)
// =====================================================================
function initVQCChart() {
    const ctx = document.getElementById("vqc-loss-chart").getContext("2d");
    
    vqcLossChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Pérdida Cuántica (VQC)",
                    data: [],
                    borderColor: "#06b6d4",
                    backgroundColor: "rgba(6, 182, 212, 0.05)",
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: "y-loss"
                },
                {
                    label: "Pérdida Clásica",
                    data: [],
                    borderColor: "#f59e0b",
                    backgroundColor: "rgba(245, 158, 11, 0.05)",
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.3,
                    yAxisID: "y-loss"
                },
                {
                    label: "Precisión Cuántica",
                    data: [],
                    borderColor: "#10b981",
                    borderWidth: 1.5,
                    pointRadius: 2,
                    tension: 0.2,
                    yAxisID: "y-acc"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.03)" },
                    title: { display: true, text: "Época", color: "#94a3b8" },
                    ticks: { color: "#94a3b8" }
                },
                "y-loss": {
                    type: "linear",
                    position: "left",
                    grid: { color: "rgba(255,255,255,0.03)" },
                    title: { display: true, text: "Pérdida (BCE)", color: "#94a3b8" },
                    ticks: { color: "#94a3b8" }
                },
                "y-acc": {
                    type: "linear",
                    position: "right",
                    grid: { display: false },
                    min: 0.0,
                    max: 1.0,
                    title: { display: true, text: "Precisión", color: "#94a3b8" },
                    ticks: { color: "#94a3b8" }
                }
            },
            plugins: {
                legend: {
                    labels: { color: "#94a3b8", font: { size: 9 } }
                }
            }
        }
    });
}

// =====================================================================
// 3. DYNAMIC QUANTUM CIRCUIT DRAWER (SVG VECTORGRAPHIC GENERATION)
// =====================================================================
function drawInitialCircuit() {
    const qubits = parseInt(document.getElementById("vqc-qubits").value);
    const layers = parseInt(document.getElementById("vqc-layers").value);
    const ansatz = document.getElementById("vqc-ansatz").value;
    const embedding = document.getElementById("vqc-embedding").value;
    
    // Draw the circuit using Javascript and SVG
    drawCircuitDiagram(qubits, layers, embedding, ansatz);
}

function drawCircuitDiagram(n_qubits, layers, embedding, ansatz) {
    const svg = document.getElementById("circuit-svg");
    svg.innerHTML = ""; // Clear existing drawings
    
    const svgWidth = svg.clientWidth || 500;
    const svgHeight = 220;
    const paddingLeft = 60;
    const paddingRight = 40;
    const paddingTop = 30;
    const usableHeight = svgHeight - paddingTop - 35;
    
    // Dynamic vertical spacing for qubits
    const qSpacing = n_qubits > 1 ? usableHeight / (n_qubits - 1) : 0;
    
    // Title card description
    const ansatzText = {
        strongly_entangling: "Capas Fuertemente Entrelazadas",
        basic: "Capas Entrelazadas Básicas (CNOT)",
        fsim_tribute: "Ansatz fsim (Tributo TFG Glicina)"
    };
    document.getElementById("ansatz-desc-txt").innerText = ansatzText[ansatz] || ansatz;

    // Helper: Draw Qubit Wires
    for (let i = 0; i < n_qubits; i++) {
        const y = paddingTop + i * qSpacing;
        
        // Qubit label
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "15");
        text.setAttribute("y", y + 4);
        text.setAttribute("fill", "#a5b4fc");
        text.setAttribute("font-family", "Outfit");
        text.setAttribute("font-size", "12");
        text.setAttribute("font-weight", "bold");
        text.textContent = `|q${i}⟩`;
        svg.appendChild(text);
        
        // Wire Line
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", paddingLeft);
        line.setAttribute("y1", y);
        line.setAttribute("x2", svgWidth - paddingRight);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "rgba(255,255,255,0.15)");
        line.setAttribute("stroke-width", "2");
        svg.appendChild(line);
    }
    
    let currentX = paddingLeft + 25;
    
    // A. Draw DATA EMBEDDING block
    const embedWidth = embedding === "angle" ? 65 : 85;
    const embedRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    embedRect.setAttribute("x", currentX);
    embedRect.setAttribute("y", paddingTop - 12);
    embedRect.setAttribute("width", embedWidth);
    embedRect.setAttribute("height", n_qubits === 1 ? 30 : qSpacing * (n_qubits - 1) + 24);
    embedRect.setAttribute("rx", "6");
    embedRect.setAttribute("fill", "rgba(6, 182, 212, 0.15)");
    embedRect.setAttribute("stroke", "#06b6d4");
    embedRect.setAttribute("stroke-width", "1.5");
    svg.appendChild(embedRect);
    
    const embedText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    embedText.setAttribute("x", currentX + embedWidth / 2);
    embedText.setAttribute("y", paddingTop + (qSpacing * (n_qubits - 1)) / 2 + 5);
    embedText.setAttribute("text-anchor", "middle");
    embedText.setAttribute("fill", "#22d3ee");
    embedText.setAttribute("font-size", "11");
    embedText.setAttribute("font-weight", "bold");
    embedText.textContent = embedding === "angle" ? "Angle [Rx]" : "Amplitude [U]";
    svg.appendChild(embedText);
    
    currentX += embedWidth + 30;
    
    // B. Draw layers of the ANSATZ
    const blockWidthPerLayer = (svgWidth - paddingRight - currentX - 45) / layers;
    
    for (let l = 0; l < layers; l++) {
        const layerX = currentX + l * blockWidthPerLayer;
        
        if (ansatz === "strongly_entangling" || ansatz === "fsim_tribute") {
            // Draw rotations per qubit
            for (let i = 0; i < n_qubits; i++) {
                const y = paddingTop + i * qSpacing;
                const gateW = 32;
                const gateH = 20;
                
                const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                r.setAttribute("x", layerX);
                r.setAttribute("y", y - gateH / 2);
                r.setAttribute("width", gateW);
                r.setAttribute("height", gateH);
                r.setAttribute("rx", "4");
                r.setAttribute("fill", "rgba(139, 92, 246, 0.2)");
                r.setAttribute("stroke", "#8b5cf6");
                r.setAttribute("stroke-width", "1");
                svg.appendChild(r);
                
                const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
                t.setAttribute("x", layerX + gateW / 2);
                t.setAttribute("y", y + 4);
                t.setAttribute("text-anchor", "middle");
                t.setAttribute("fill", "#c084fc");
                t.setAttribute("font-size", "8");
                t.setAttribute("font-weight", "bold");
                t.textContent = ansatz === "strongly_entangling" ? "Rot" : "f_φ";
                svg.appendChild(t);
            }
            
            // Draw entangling gates
            if (n_qubits > 1) {
                const entangleX = layerX + 38;
                if (ansatz === "strongly_entangling") {
                    // Strongly Entangling uses shifted CNOTs
                    for (let i = 0; i < n_qubits; i++) {
                        const target = (i + l + 1) % n_qubits;
                        drawCNOT(svg, entangleX, paddingTop + i * qSpacing, paddingTop + target * qSpacing);
                    }
                } else if (ansatz === "fsim_tribute") {
                    // fsim / Cfsim uses double particle exchange bonds (similar to Jordan Wigner molecular lines!)
                    for (let i = 0; i < n_qubits - 1; i += 2) {
                        drawFSimGate(svg, entangleX, paddingTop + i * qSpacing, paddingTop + (i + 1) * qSpacing);
                    }
                }
            }
        } else if (ansatz === "basic") {
            // Basic Ansatz: Single rotation + CNOT ring
            for (let i = 0; i < n_qubits; i++) {
                const y = paddingTop + i * qSpacing;
                const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                r.setAttribute("x", layerX);
                r.setAttribute("y", y - 10);
                r.setAttribute("width", 26);
                r.setAttribute("height", 20);
                r.setAttribute("rx", "4");
                r.setAttribute("fill", "rgba(139, 92, 246, 0.15)");
                r.setAttribute("stroke", "#a78bfa");
                svg.appendChild(r);
                
                const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
                t.setAttribute("x", layerX + 13);
                t.setAttribute("y", y + 4);
                t.setAttribute("text-anchor", "middle");
                t.setAttribute("fill", "#c084fc");
                t.setAttribute("font-size", "9");
                t.textContent = "RY";
                svg.appendChild(t);
            }
            
            if (n_qubits > 1) {
                const cnotX = layerX + 35;
                for (let i = 0; i < n_qubits; i++) {
                    drawCNOT(svg, cnotX + i * 4, paddingTop + i * qSpacing, paddingTop + ((i + 1) % n_qubits) * qSpacing);
                }
            }
        }
    }
    
    // C. Draw MEASUREMENT METERS at the right edge
    const measureX = svgWidth - paddingRight - 15;
    for (let i = 0; i < n_qubits; i++) {
        const y = paddingTop + i * qSpacing;
        
        // Measure box
        const mBox = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        mBox.setAttribute("x", measureX);
        mBox.setAttribute("y", y - 10);
        mBox.setAttribute("width", 20);
        mBox.setAttribute("height", 20);
        mBox.setAttribute("rx", "3");
        mBox.setAttribute("fill", "#1e293b");
        mBox.setAttribute("stroke", "#64748b");
        svg.appendChild(mBox);
        
        // Meter curve
        const mPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
        mPath.setAttribute("d", `M ${measureX + 4} ${y + 5} A 7 7 0 0 1 ${measureX + 16} ${y + 5}`);
        mPath.setAttribute("fill", "none");
        mPath.setAttribute("stroke", "#94a3b8");
        mPath.setAttribute("stroke-width", "1.5");
        svg.appendChild(mPath);
        
        // Meter arrow
        const mArrow = document.createElementNS("http://www.w3.org/2000/svg", "line");
        mArrow.setAttribute("x1", measureX + 10);
        mArrow.setAttribute("y1", y + 7);
        mArrow.setAttribute("x2", measureX + 16);
        mArrow.setAttribute("y2", y - 4);
        mArrow.setAttribute("stroke", "#22d3ee");
        mArrow.setAttribute("stroke-width", "1.5");
        svg.appendChild(mArrow);
    }
}

// Helpers for drawing CNOT and FSim symbols
function drawCNOT(svg, x, yControl, yTarget) {
    // Control dot
    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("cx", x);
    dot.setAttribute("cy", yControl);
    dot.setAttribute("r", "3.5");
    dot.setAttribute("fill", "#8b5cf6");
    svg.appendChild(dot);
    
    // Vertical line
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x);
    line.setAttribute("y1", yControl);
    line.setAttribute("x2", x);
    line.setAttribute("y2", yTarget);
    line.setAttribute("stroke", "#8b5cf6");
    line.setAttribute("stroke-width", "1.5");
    svg.appendChild(line);
    
    // Target outer circle
    const circ = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circ.setAttribute("cx", x);
    circ.setAttribute("cy", yTarget);
    circ.setAttribute("r", "6");
    circ.setAttribute("fill", "none");
    circ.setAttribute("stroke", "#8b5cf6");
    circ.setAttribute("stroke-width", "1.5");
    svg.appendChild(circ);
    
    // Target horizontal cross line
    const lH = document.createElementNS("http://www.w3.org/2000/svg", "line");
    lH.setAttribute("x1", x - 6);
    lH.setAttribute("y1", yTarget);
    lH.setAttribute("x2", x + 6);
    lH.setAttribute("y2", yTarget);
    lH.setAttribute("stroke", "#8b5cf6");
    lH.setAttribute("stroke-width", "1.5");
    svg.appendChild(lH);
    
    // Target vertical cross line
    const lV = document.createElementNS("http://www.w3.org/2000/svg", "line");
    lV.setAttribute("x1", x);
    lV.setAttribute("y1", yTarget - 6);
    lV.setAttribute("x2", x);
    lV.setAttribute("y2", yTarget + 6);
    lV.setAttribute("stroke", "#8b5cf6");
    lV.setAttribute("stroke-width", "1.5");
    svg.appendChild(lV);
}

function drawFSimGate(svg, x, y1, y2) {
    // Draws a beautiful connection block indicating an FSim interaction
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x);
    line.setAttribute("y1", y1);
    line.setAttribute("x2", x);
    line.setAttribute("y2", y2);
    line.setAttribute("stroke", "#06b6d4");
    line.setAttribute("stroke-width", "2");
    line.setAttribute("stroke-dasharray", "3,2");
    svg.appendChild(line);
    
    // Box on Qubit 1
    const r1 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    r1.setAttribute("x", x - 6);
    r1.setAttribute("y", y1 - 6);
    r1.setAttribute("width", 12);
    r1.setAttribute("height", 12);
    r1.setAttribute("rx", "2");
    r1.setAttribute("fill", "rgba(6, 182, 212, 0.4)");
    r1.setAttribute("stroke", "#06b6d4");
    svg.appendChild(r1);
    
    // Box on Qubit 2
    const r2 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    r2.setAttribute("x", x - 6);
    r2.setAttribute("y", y2 - 6);
    r2.setAttribute("width", 12);
    r2.setAttribute("height", 12);
    r2.setAttribute("rx", "2");
    r2.setAttribute("fill", "rgba(6, 182, 212, 0.4)");
    r2.setAttribute("stroke", "#06b6d4");
    svg.appendChild(r2);
}

// =====================================================================
// 4. DATASET LOADER & INITIAL DRAWINGS
// =====================================================================
async function loadInitialDataset() {
    const datasetType = document.getElementById("vqc-dataset").value;
    try {
        const response = await fetch(`/api/dataset?type=${datasetType}&samples=60&noise=0.12`);
        const result = await response.json();
        
        if (result.status === "success") {
            currentDatasetData = result.data;
            // Draw empty boundaries with these data points loaded
            drawDecisionBoundary(null, null); 
        }
    } catch (e) {
        console.error("Error loading initial dataset:", e);
    }
}

// =====================================================================
// 5. VARIATIONAL QUANTUM CLASSIFIER (VQC) TRAINING ENGINE (SSE STREAM)
// =====================================================================
function startVQCTraining() {
    const btn = document.getElementById("btn-start-vqc");
    
    // If already running, cancel the stream
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Entrenar Modelos Híbridos`;
        btn.classList.remove("btn-cancel");
        document.getElementById("vqc-state-txt").innerText = "Cancelado";
        return;
    }
    
    // Prepare values from DOM
    const dataset = document.getElementById("vqc-dataset").value;
    const qubits = document.getElementById("vqc-qubits").value;
    const layers = document.getElementById("vqc-layers").value;
    const embedding = document.getElementById("vqc-embedding").value;
    const ansatz = document.getElementById("vqc-ansatz").value;
    const lr = document.getElementById("vqc-lr").value;
    const epochs = document.getElementById("vqc-epochs").value;
    const baseline = document.getElementById("vqc-baseline").value;
    
    // Redraw circuit to match exact configurations
    drawCircuitDiagram(parseInt(qubits), parseInt(layers), embedding, ansatz);
    
    // Reset loss chart data arrays
    vqcLossChart.data.labels = [];
    vqcLossChart.data.datasets[0].data = [];
    vqcLossChart.data.datasets[1].data = [];
    vqcLossChart.data.datasets[2].data = [];
    vqcLossChart.update();
    
    // Set UI training states
    btn.innerHTML = `<i class="fa-solid fa-stop"></i> Detener Simulación`;
    btn.classList.add("btn-cancel");
    document.getElementById("vqc-state-txt").innerText = "Simulando...";
    document.getElementById("vqc-loss-txt").innerText = "Iniciando...";
    document.getElementById("vqc-acc-txt").innerText = "Calculando...";
    document.getElementById("cvc-acc-txt").innerText = "Calculando...";
    
    // Create query string
    const query = `dataset=${dataset}&qubits=${qubits}&layers=${layers}&embedding=${embedding}&ansatz=${ansatz}&lr=${lr}&epochs=${epochs}&samples=40&baseline=${baseline}`;
    
    // Establish Server-Sent Events link
    eventSource = new EventSource(`/api/vqc/train?${query}`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.status === "start") {
            document.getElementById("vqc-state-txt").innerText = "Entrenando...";
        } else if (data.status === "training") {
            // Update stats cards
            document.getElementById("vqc-loss-txt").innerText = data.q_loss.toFixed(4);
            document.getElementById("vqc-acc-txt").innerText = `${(data.q_test_acc * 100).toFixed(0)}%`;
            document.getElementById("cvc-acc-txt").innerText = `${(data.c_acc * 100).toFixed(0)}%`;
            
            // Push values onto training charts
            vqcLossChart.data.labels.push(data.epoch);
            vqcLossChart.data.datasets[0].data.push(data.q_loss);
            vqcLossChart.data.datasets[1].data.push(data.c_loss);
            vqcLossChart.data.datasets[2].data.push(data.q_test_acc);
            vqcLossChart.update();
            
            // Draw VQC 2D boundary
            drawDecisionBoundary(data.q_grid, data.bounds);
        } else if (data.status === "completed") {
            document.getElementById("vqc-state-txt").innerText = "Finalizado";
            closeVQCSession();
        }
    };
    
    eventSource.onerror = (err) => {
        console.error("SSE Stream Error:", err);
        document.getElementById("vqc-state-txt").innerText = "Error";
        closeVQCSession();
    };
}

function closeVQCSession() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    const btn = document.getElementById("btn-start-vqc");
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Entrenar Modelos Híbridos`;
    btn.classList.remove("btn-cancel");
}

// =====================================================================
// 6. CANVAS DECISION BOUNDARY INTERPOLATED RENDERING
// =====================================================================
function drawDecisionBoundary(gridPreds, bounds) {
    const canvas = document.getElementById("qml-boundary-canvas");
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // A. Draw background gradient based on VQC grid predictions
    if (gridPreds && bounds) {
        const gridRes = 15; // 15x15 prediction mesh
        const blockW = w / gridRes;
        const blockH = h / gridRes;
        
        let pIndex = 0;
        for (let i = 0; i < gridRes; i++) {
            for (let j = 0; j < gridRes; j++) {
                const prob = gridPreds[pIndex];
                pIndex++;
                
                // Map probabilities to a sleek color scale:
                // prob -> 0.0 is red (Class 0), 1.0 is cyan (Class 1)
                let r, g, b, alpha;
                if (prob < 0.5) {
                    // Class 0: Red scale
                    const factor = (0.5 - prob) * 2; // 0 (near 0.5) to 1 (near 0.0)
                    r = 239; g = 68; b = 68;
                    alpha = 0.1 + factor * 0.25;
                } else {
                    // Class 1: Cyan scale
                    const factor = (prob - 0.5) * 2; // 0 to 1
                    r = 6; g = 182; b = 212;
                    alpha = 0.1 + factor * 0.25;
                }
                
                ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
                // Mesh grid predictions are row-by-row, column-by-column.
                // We reverse-map block layout coordinates:
                // Grid points are generated with y ascending then x ascending, or xx.ravel(), yy.ravel().
                // meshgrid outputs column-major flattened.
                // Let's draw blocks corresponding to their column indexes:
                ctx.fillRect(j * blockW, (gridRes - 1 - i) * blockH, blockW, blockH);
            }
        }
    } else {
        // Draw standard empty background
        ctx.fillStyle = "rgba(7, 9, 19, 0.4)";
        ctx.fillRect(0, 0, w, h);
    }
    
    // Draw canvas border
    ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, w, h);
    
    // B. Draw dataset points overlaid on top of the boundary
    if (currentDatasetData.length > 0) {
        // Calculate dynamic scaling factors based on bounds (or fit default scales)
        let xMin = -2.0, xMax = 2.0, yMin = -2.0, yMax = 2.0;
        if (bounds) {
            xMin = bounds.x_min; xMax = bounds.x_max;
            yMin = bounds.y_min; yMax = bounds.y_max;
        } else {
            // Calculate dataset bounds
            const xs = currentDatasetData.map(d => d.x);
            const ys = currentDatasetData.map(d => d.y);
            xMin = Math.min(...xs) - 0.3; xMax = Math.max(...xs) + 0.3;
            yMin = Math.min(...ys) - 0.3; yMax = Math.max(...ys) + 0.3;
        }
        
        currentDatasetData.forEach(pt => {
            // Map coordinates to canvas space
            const cx = ((pt.x - xMin) / (xMax - xMin)) * w;
            const cy = h - ((pt.y - yMin) / (yMax - yMin)) * h; // invert y for canvas drawing
            
            ctx.beginPath();
            ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
            
            if (pt.label === 0) {
                // Class 0: glowing solid red circle
                ctx.fillStyle = "#ef4444";
                ctx.shadowColor = "rgba(239, 68, 68, 0.8)";
                ctx.shadowBlur = 6;
            } else {
                // Class 1: glowing solid cyan circle
                ctx.fillStyle = "#06b6d4";
                ctx.shadowColor = "rgba(6, 182, 212, 0.8)";
                ctx.shadowBlur = 6;
            }
            ctx.fill();
            
            // Draw a subtle dark outline for contrast
            ctx.shadowBlur = 0; // reset glow
            ctx.strokeStyle = "#070913";
            ctx.lineWidth = 1;
            ctx.stroke();
        });
    }
}

// =====================================================================
// 7. QUANTUM KERNELS & QUANTUM SVM (QSVM) OPERATIONS
// =====================================================================
async function calculateQuantumKernel() {
    const btn = document.getElementById("btn-start-qsvm");
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Computando en PennyLane...`;
    btn.setAttribute("disabled", "true");
    
    // Fetch settings
    const dataset = document.getElementById("qsvm-dataset").value;
    const qubits = document.getElementById("qsvm-qubits").value;
    const embedding = document.getElementById("qsvm-embedding").value;
    const c = document.getElementById("qsvm-c").value;
    
    document.getElementById("qsvm-hilbert-txt").innerHTML = `2<sup>${qubits}</sup> = ${Math.pow(2, parseInt(qubits))}`;

    try {
        const response = await fetch("/api/qsvm/kernel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dataset, qubits: parseInt(qubits), embedding, C: parseFloat(c), samples: 40 })
        });
        const result = await response.json();
        
        if (result.status === "success") {
            // Update stats
            document.getElementById("qsvm-acc-txt").innerText = `${(result.q_test_acc * 100).toFixed(0)}%`;
            document.getElementById("csvm-acc-txt").innerText = `${(result.c_test_acc * 100).toFixed(0)}%`;
            
            // A. Draw Kernel Heatmap Matrix
            drawKernelHeatmap(result.q_kernel_matrix);
            
            // B. Draw side-by-side decision boundaries
            drawQSVMBoundary(document.getElementById("qsvm-boundary-canvas"), result.q_grid, result.train_points, result.test_points, result.bounds);
            drawQSVMBoundary(document.getElementById("csvm-boundary-canvas"), result.c_grid, result.train_points, result.test_points, result.bounds);
        } else {
            alert("Error in kernel calculation: " + result.message);
        }
    } catch (e) {
        console.error("QSVM request error:", e);
        alert("Error executing Kernel calculation. Ensure uvicorn server is active.");
    } finally {
        btn.innerHTML = `<i class="fa-solid fa-network-wired"></i> Calcular Núcleo Cuántico`;
        btn.removeAttribute("disabled");
    }
}

// Draw the pairwise transition overlap kernel matrix as a beautiful pixels heatmap
function drawKernelHeatmap(matrix) {
    const canvas = document.getElementById("qsvm-heatmap-canvas");
    const ctx = canvas.getContext("2d");
    const size = canvas.width;
    const n = matrix.length;
    const step = size / n;
    
    ctx.clearRect(0, 0, size, size);
    
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            const val = matrix[i][j]; // overlap value [0.0, 1.0]
            
            // Color map gradient: Black (0.0) -> Purple -> Cyan -> White (1.0)
            let r, g, b;
            if (val < 0.2) {
                // black to dark purple
                const f = val / 0.2;
                r = Math.floor(f * 30);
                g = Math.floor(f * 10);
                b = Math.floor(f * 80);
            } else if (val < 0.6) {
                // purple to cyan
                const f = (val - 0.2) / 0.4;
                r = Math.floor(30 + f * (6 - 30));
                g = Math.floor(10 + f * (182 - 10));
                b = Math.floor(80 + f * (212 - 80));
            } else {
                // cyan to white
                const f = (val - 0.6) / 0.4;
                r = Math.floor(6 + f * (255 - 6));
                g = Math.floor(182 + f * (255 - 182));
                b = Math.floor(212 + f * (255 - 212));
            }
            
            ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            ctx.fillRect(j * step, i * step, step, step);
            
            // Add extremely subtle border around cells
            ctx.strokeStyle = "rgba(255,255,255,0.015)";
            ctx.strokeRect(j * step, i * step, step, step);
        }
    }
}

// Draws the final QSVM / SVM decision boundaries on their respective canvases
function drawQSVMBoundary(canvas, gridPreds, trainPoints, testPoints, bounds) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // A. Draw prediction background
    const gridRes = 15;
    const blockW = w / gridRes;
    const blockH = h / gridRes;
    
    let pIndex = 0;
    for (let i = 0; i < gridRes; i++) {
        for (let j = 0; j < gridRes; j++) {
            const prob = gridPreds[pIndex];
            pIndex++;
            
            let r, g, b, alpha;
            if (prob < 0.5) {
                const factor = (0.5 - prob) * 2;
                r = 239; g = 68; b = 68;
                alpha = 0.1 + factor * 0.22;
            } else {
                const factor = (prob - 0.5) * 2;
                r = 6; g = 182; b = 212;
                alpha = 0.1 + factor * 0.22;
            }
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            ctx.fillRect(j * blockW, (gridRes - 1 - i) * blockH, blockW, blockH);
        }
    }
    
    // Draw canvas border
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.strokeRect(0, 0, w, h);
    
    // B. Draw points (Train as circles, Test as glowing squares for recruiter wow factor!)
    const xMin = bounds.x_min; const xMax = bounds.x_max;
    const yMin = bounds.y_min; const yMax = bounds.y_max;
    
    // Render train points
    trainPoints.forEach(pt => {
        const cx = ((pt.x - xMin) / (xMax - xMin)) * w;
        const cy = h - ((pt.y - yMin) / (yMax - yMin)) * h;
        
        ctx.beginPath();
        ctx.arc(cx, cy, 3.5, 0, 2 * Math.PI);
        ctx.fillStyle = pt.label === 0 ? "#ef4444" : "#06b6d4";
        ctx.fill();
        ctx.strokeStyle = "#070913";
        ctx.stroke();
    });
    
    // Render test points as glowing squares
    testPoints.forEach(pt => {
        const cx = ((pt.x - xMin) / (xMax - xMin)) * w;
        const cy = h - ((pt.y - yMin) / (yMax - yMin)) * h;
        
        ctx.fillStyle = pt.label === 0 ? "#ef4444" : "#06b6d4";
        ctx.shadowColor = pt.label === 0 ? "rgba(239,68,68,0.8)" : "rgba(6,182,212,0.8)";
        ctx.shadowBlur = 5;
        
        ctx.fillRect(cx - 3.5, cy - 3.5, 7, 7);
        
        ctx.shadowBlur = 0;
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 0.5;
        ctx.strokeRect(cx - 3.5, cy - 3.5, 7, 7);
    });
}

// Draw initial placeholders for empty boundary boxes
function drawEmptyQSVMHeatmap() {
    const canvas = document.getElementById("qsvm-heatmap-canvas");
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "rgba(7,9,19,0.5)";
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = "#8892b0";
    ctx.font = "12px Outfit";
    ctx.textAlign = "center";
    ctx.fillText("Presiona 'Calcular' para compilar el núcleo", canvas.width/2, canvas.height/2);
}

function drawEmptyQSVMBoundaries() {
    const canvases = [
        document.getElementById("qsvm-boundary-canvas"),
        document.getElementById("csvm-boundary-canvas")
    ];
    canvases.forEach(canvas => {
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "rgba(7,9,19,0.5)";
        ctx.fillRect(0,0,canvas.width,canvas.height);
        ctx.fillStyle = "#64748b";
        ctx.font = "10px Outfit";
        ctx.textAlign = "center";
        ctx.fillText("Espere los resultados...", canvas.width/2, canvas.height/2);
    });
}
