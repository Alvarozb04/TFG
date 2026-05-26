import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from sklearn.datasets import make_moons, make_circles
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Import our custom quantum and classical modules (pure NumPy & PennyLane)
from qml_models import VQCModel, QuantumKernelMachine, get_molecular_hamiltonian_simulation_concept
from classical_models import ClassicalBaselines

app = FastAPI(
    title="Quantum Machine Learning Sandbox",
    description="FastAPI Backend for QML training, QSVM kernels, and Portfolio presentation.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Helper function to generate datasets
def generate_dataset(dataset_type="circle", n_samples=60, noise=0.1):
    """
    Generates beautiful 2D datasets suitable for quantum and classical classification.
    """
    if dataset_type == "circle":
        X, y = make_circles(n_samples=n_samples, noise=noise, factor=0.5, random_state=42)
    elif dataset_type == "moons":
        X, y = make_moons(n_samples=n_samples, noise=noise, random_state=42)
    elif dataset_type == "linear":
        np.random.seed(42)
        X = np.random.rand(n_samples, 2) * 2 - 1
        y = np.array([1 if x[0] + x[1] > 0.1 else 0 for x in X])
    else:
        X, y = make_moons(n_samples=n_samples, noise=noise, random_state=42)
        
    # Scale features to prevent quantum circuit over-rotation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_normalized = np.clip(X_scaled, -1.5, 1.5) * (np.pi / 3.0) # Map to roughly [-pi/2, pi/2]
    
    return X_normalized, y

# Endpoint to fetch datasets directly for front-end rendering
@app.get("/api/dataset")
def get_dataset(type: str = "circle", samples: int = 60, noise: float = 0.1):
    try:
        X, y = generate_dataset(type, samples, noise)
        data = [
            {"x": float(X[i, 0]), "y": float(X[i, 1]), "label": int(y[i])}
            for i in range(len(X))
        ]
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# Endpoint to stream VQC training updates in real time using Server-Sent Events (SSE)
@app.get("/api/vqc/train")
def train_vqc(
    dataset: str = "circle",
    qubits: int = 4,
    layers: int = 2,
    embedding: str = "angle",
    ansatz: str = "strongly_entangling",
    lr: float = 0.05,
    epochs: int = 20,
    samples: int = 40,
    baseline: str = "mlp"
):
    """
    Trains the Quantum VQC and Classical baseline models concurrently,
    streaming epoch-by-epoch loss, accuracy, and decision boundaries.
    """
    X, y = generate_dataset(dataset, samples, 0.1)
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    
    # Create the Decision boundary grid (15x15 mesh) to predict boundaries
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 15), np.linspace(y_min, y_max, 15))
    grid_points = np.c_[xx.ravel(), yy.ravel()]

    # Instantiate QML VQC Model (PennyLane Native Autograd)
    q_model = VQCModel(n_qubits=qubits, layers=layers, embedding_type=embedding, ansatz_type=ansatz, lr=lr)

    # Classical Counterpart baseline
    c_model = ClassicalBaselines(model_type=baseline, hidden_layer_sizes=(8, 4), learning_rate=lr, epochs=epochs)
    c_metrics = c_model.fit(X_train, y_train)
    c_grid_preds = c_model.predict_proba(grid_points)

    async def event_generator():
        yield f"data: {json.dumps({'status': 'start', 'message': 'Quantum training initialized'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Training loop
        for epoch in range(epochs):
            # Run a single optimization epoch in PennyLane using Adam
            loss = q_model.train_step(X_train, y_train)
            
            # Predict and evaluate accuracies using standard numpy arrays
            q_train_preds = q_model.predict_proba(X_train)
            train_acc = np.mean((np.array(q_train_preds) >= 0.5).astype(int) == y_train)
            
            q_test_preds = q_model.predict_proba(X_test)
            test_acc = np.mean((np.array(q_test_preds) >= 0.5).astype(int) == y_test)
            
            # Compute grid predictions for decision boundary visualizer
            q_grid_preds = q_model.predict_proba(grid_points)
                
            # Fetch classical metrics for this epoch (precomputed)
            c_loss = c_metrics["loss"][epoch] if epoch < len(c_metrics["loss"]) else c_metrics["loss"][-1]
            c_acc = c_metrics["accuracy"][epoch] if epoch < len(c_metrics["accuracy"]) else c_metrics["accuracy"][-1]

            # Send epoch update to frontend
            epoch_data = {
                "status": "training",
                "epoch": epoch + 1,
                "q_loss": float(loss),
                "q_train_acc": float(train_acc),
                "q_test_acc": float(test_acc),
                "q_grid": q_grid_preds,
                "c_loss": float(c_loss),
                "c_acc": float(c_acc),
                "c_grid": c_grid_preds,
                "bounds": {"x_min": float(x_min), "x_max": float(x_max), "y_min": float(y_min), "y_max": float(y_max)}
            }
            
            yield f"data: {json.dumps(epoch_data)}\n\n"
            # Small delay to allow the frontend to draw smoothly
            await asyncio.sleep(0.02)

        # Done streaming
        yield f"data: {json.dumps({'status': 'completed', 'message': 'Quantum-Classical hybrid training finished.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Endpoint for Quantum SVM (QSVM) Kernel calculations and SVM fitting
@app.post("/api/qsvm/kernel")
async def calculate_qsvm_kernel(request: Request):
    """
    Computes pairwise Quantum Kernel matrix and trains a classical SVM with it.
    Returns heatmaps of the Quantum Kernel and classification boundaries.
    """
    try:
        body = await request.json()
        dataset = body.get("dataset", "circle")
        qubits = body.get("qubits", 2)
        embedding = body.get("embedding", "angle")
        samples = body.get("samples", 40)
        c_param = body.get("C", 1.0)
        
        # 1. Generate data
        X, y = generate_dataset(dataset, samples, 0.15)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        
        # 2. Setup Quantum Kernel Machine
        q_kernel_machine = QuantumKernelMachine(n_qubits=qubits, embedding_type=embedding)
        
        # 3. Compute Train Kernel Matrix (pair-wise transition amplitudes)
        K_train = q_kernel_machine.fit_kernel_matrix(X_train, X_train)
        K_test = q_kernel_machine.fit_kernel_matrix(X_test, X_train)
        
        # 4. Fit SVC using precomputed Quantum Kernel
        clf = SVC(kernel="precomputed", C=c_param, probability=True)
        clf.fit(K_train, y_train)
        
        # 5. Evaluate accuracies
        train_preds = clf.predict(K_train)
        test_preds = clf.predict(K_test)
        
        train_acc = float(np.mean(train_preds == y_train))
        test_acc = float(np.mean(test_preds == y_test))
        
        # 6. Predict decision boundary over a mesh grid
        x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
        y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 15), np.linspace(y_min, y_max, 15))
        grid_points = np.c_[xx.ravel(), yy.ravel()]
        
        # Compute Kernel between grid points and training points
        K_grid = q_kernel_machine.fit_kernel_matrix(grid_points, X_train)
        grid_preds = clf.predict_proba(K_grid)[:, 1].tolist()
        
        # 7. Compare with a classical SVM (RBF Kernel)
        classical_svm = SVC(kernel="rbf", C=c_param, probability=True)
        classical_svm.fit(X_train, y_train)
        c_train_acc = float(classical_svm.score(X_train, y_train))
        c_test_acc = float(classical_svm.score(X_test, y_test))
        c_grid_preds = classical_svm.predict_proba(grid_points)[:, 1].tolist()

        return JSONResponse(content={
            "status": "success",
            "q_train_acc": train_acc,
            "q_test_acc": test_acc,
            "q_kernel_matrix": K_train.tolist(),
            "q_grid": grid_preds,
            "c_train_acc": c_train_acc,
            "c_test_acc": c_test_acc,
            "c_grid": c_grid_preds,
            "train_points": [{"x": float(X_train[i, 0]), "y": float(X_train[i, 1]), "label": int(y_train[i])} for i in range(len(X_train))],
            "test_points": [{"x": float(X_test[i, 0]), "y": float(X_test[i, 1]), "label": int(y_test[i])} for i in range(len(X_test))],
            "bounds": {"x_min": float(x_min), "x_max": float(x_max), "y_min": float(y_min), "y_max": float(y_max)}
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# Endpoint for User TFG Glycine simulation specs (Portfolio tab helper)
@app.get("/api/tfg/glycine")
def get_tfg_glycine_details():
    try:
        details = get_molecular_hamiltonian_simulation_concept()
        return JSONResponse(content={"status": "success", "data": details})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# Serve the static UI files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
