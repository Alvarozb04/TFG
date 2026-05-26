import pennylane as qml
from pennylane import numpy as pnp
import numpy as np

# =====================================================================
# 1. VARIATIONAL QUANTUM CLASSIFIER (VQC)
# =====================================================================

def get_vqc_circuit(n_qubits=4, layers=2, embedding_type="angle", ansatz_type="strongly_entangling"):
    """
    Dynamically creates and returns a PennyLane QNode.
    Using autograd interface for lightning-fast numpy optimization.
    """
    dev = qml.device("default.qubit", wires=n_qubits)
    
    # Define the embedding function
    def embed_data(x):
        if embedding_type == "angle":
            qml.AngleEmbedding(x, wires=range(n_qubits), rotation="X")
        elif embedding_type == "amplitude":
            # Normalization padding handled externally or via PennyLane
            qml.AmplitudeEmbedding(x, wires=range(n_qubits), pad_with=0.0, normalize=True)
        else:
            qml.AngleEmbedding(x, wires=range(n_qubits), rotation="X")

    # Define the ansatz (parameterized quantum circuit)
    def ansatz(weights):
        if ansatz_type == "basic":
            for l in range(layers):
                for i in range(n_qubits):
                    qml.RY(weights[l, i], wires=i)
                if n_qubits > 1:
                    for i in range(n_qubits):
                        qml.CNOT(wires=[i, (i + 1) % n_qubits])
                        
        elif ansatz_type == "strongly_entangling":
            qml.StronglyEntanglingLayers(weights, wires=range(n_qubits))
            
        elif ansatz_type == "fsim_tribute":
            """
            FERMIONIC SIMULATION ANSATZ - TFG TRIBUTE
            Custom Cfsim (Fermionic Simulation) inspired entangling layers.
            """
            for l in range(layers):
                for i in range(n_qubits):
                    qml.RX(weights[l, i, 0], wires=i)
                    qml.RZ(weights[l, i, 1], wires=i)
                
                if n_qubits > 1:
                    for i in range(0, n_qubits - 1, 2):
                        qml.IsingXX(weights[l, i, 2], wires=[i, i+1])
                        qml.IsingYY(weights[l, i, 2], wires=[i, i+1])
                        qml.IsingZZ(weights[l, i, 3] if weights.shape[2] > 3 else 0.1, wires=[i, i+1])
                    for i in range(1, n_qubits - 1, 2):
                        qml.IsingXX(weights[l, i, 2], wires=[i, i+1])
                        qml.IsingYY(weights[l, i, 2], wires=[i, i+1])
                        qml.IsingZZ(weights[l, i, 3] if weights.shape[2] > 3 else 0.1, wires=[i, i+1])

    @qml.qnode(dev, interface="autograd")
    def circuit(x, weights):
        embed_data(x)
        ansatz(weights)
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

    return circuit

class VQCModel:
    """
    Model wrapper using PennyLane's Autograd numpy interface.
    Provides training step execution without requiring large PyTorch packages.
    """
    def __init__(self, n_qubits=4, layers=2, embedding_type="angle", ansatz_type="strongly_entangling", lr=0.05):
        self.n_qubits = n_qubits
        self.layers = layers
        self.embedding_type = embedding_type
        self.ansatz_type = ansatz_type
        
        self.circuit = get_vqc_circuit(n_qubits, layers, embedding_type, ansatz_type)
        
        # Initialize quantum weights with pennylane.numpy (enables autodiff gradients)
        if ansatz_type == "basic":
            self.weights = pnp.array(np.random.rand(layers, n_qubits) * 2 * np.pi, requires_grad=True)
        elif ansatz_type == "strongly_entangling":
            self.weights = pnp.array(np.random.rand(layers, n_qubits, 3) * 2 * np.pi, requires_grad=True)
        elif ansatz_type == "fsim_tribute":
            self.weights = pnp.array(np.random.rand(layers, n_qubits, 4) * 2 * np.pi, requires_grad=True)
            
        self.bias = pnp.array(0.0, requires_grad=True)
        self.opt = qml.AdamOptimizer(stepsize=lr)
        
    def sigmoid(self, x):
        return 1.0 / (1.0 + pnp.exp(-x * 2.5))
        
    def predict_sample(self, x, weights, bias):
        # Forward pass on single sample
        q_out = self.circuit(x, weights)
        # Average expectation value + bias
        val = pnp.mean(q_out) + bias
        return self.sigmoid(val)
        
    def cost(self, params, X, y):
        """
        Binary Cross Entropy (BCE) cost function.
        params is a tuple (weights, bias) for PennyLane optimizers to update simultaneously.
        """
        weights, bias = params
        loss = 0.0
        for i in range(len(X)):
            pred = self.predict_sample(X[i], weights, bias)
            # Clip predictions to prevent infinite log values
            pred = pnp.clip(pred, 1e-15, 1.0 - 1e-15)
            loss += - (y[i] * pnp.log(pred) + (1.0 - y[i]) * pnp.log(1.0 - pred))
        return loss / len(X)
        
    def train_step(self, X, y):
        """
        Runs one step of the Adam Optimizer, updating weights and bias in place.
        """
        params = (self.weights, self.bias)
        # step_and_cost automatically differentiates our cost function
        new_params, loss_val = self.opt.step_and_cost(self.cost, params, X=X, y=y)
        self.weights, self.bias = new_params
        return float(loss_val)
        
    def predict_proba(self, X):
        """
        Returns probabilities of class 1 for a list of samples.
        """
        probs = []
        for x in X:
            prob = self.predict_sample(x, self.weights, self.bias)
            probs.append(float(prob))
        return probs

# =====================================================================
# 2. QUANTUM KERNELS & QUANTUM SVM (QSVM)
# =====================================================================

class QuantumKernelMachine:
    """
    Computes a Quantum Kernel matrix using custom feature maps.
    Calculates wage function overlap as transition probabilities.
    """
    def __init__(self, n_qubits=2, embedding_type="angle"):
        self.n_qubits = n_qubits
        self.embedding_type = embedding_type
        self.dev = qml.device("default.qubit", wires=n_qubits)
        
        @qml.qnode(self.dev, interface="autograd")
        def kernel_circuit(x1, x2):
            if self.embedding_type == "angle":
                qml.AngleEmbedding(x1, wires=range(self.n_qubits), rotation="X")
                for i in range(self.n_qubits - 1):
                    qml.CNOT(wires=[i, i+1])
            elif self.embedding_type == "amplitude":
                qml.AmplitudeEmbedding(x1, wires=range(self.n_qubits), pad_with=0.0, normalize=True)
            
            if self.embedding_type == "angle":
                for i in reversed(range(self.n_qubits - 1)):
                    qml.CNOT(wires=[i, i+1])
                qml.adjoint(qml.AngleEmbedding)(x2, wires=range(self.n_qubits), rotation="X")
            elif self.embedding_type == "amplitude":
                qml.adjoint(qml.AmplitudeEmbedding)(x2, wires=range(self.n_qubits), pad_with=0.0, normalize=True)
                
            return qml.probs(wires=range(self.n_qubits))
            
        self.kernel_circuit = kernel_circuit
        
    def compute_kernel_element(self, x1, x2):
        probs = self.kernel_circuit(x1, x2)
        return float(probs[0])
        
    def fit_kernel_matrix(self, X1, X2):
        N = len(X1)
        M = len(X2)
        K = np.zeros((N, M))
        for i in range(N):
            for j in range(M):
                if X1 is X2 and j < i:
                    K[i, j] = K[j, i]
                else:
                    K[i, j] = self.compute_kernel_element(X1[i], X2[j])
        return K

# =====================================================================
# 3. MOLECULAR SIMULATION TRIBUTE HELPER
# =====================================================================
def get_molecular_hamiltonian_simulation_concept():
    return {
        "glycine_formula": "C2H5NO2",
        "description": (
            "En tu Trabajo de Fin de Grado (TFG), realizaste la simulación cuántica de la molécula de glicina. "
            "Para ello, mapeaste los operadores fermiónicos del Hamiltoniano molecular a operadores de spin (qubits) "
            "mediante las transformaciones de Jordan-Wigner y Parity Mapping. El uso de compuertas Cfsim (Current "
            "Fermionic Simulation) permite modelar con precisión los intercambios de excitación de partículas de "
            "manera eficiente en hardware cuántico (especialmente en arquitecturas como el chip Sycamore de Google)."
        ),
        "jordan_wigner_math": (
            "La transformación de Jordan-Wigner mapea operadores fermiónicos a operadores de Pauli:\n"
            "c_j^\\dagger = I^{\\otimes j-1} \\otimes \\sigma_- \\otimes \\sigma_z^{\\otimes N-j}\n"
            "Esto mantiene las relaciones de anticonmutación fermiónica a través de cadenas de operadores Pauli-Z."
        ),
        "cfsim_matrix": (
            "La compuerta FSim/Cfsim (Fermionic Simulation) está definida en la base de dos qubits {|00>, |01>, |10>, |11>} como:\n"
            "FSim(\\theta, \\phi) = [\n"
            "  [1, 0, 0, 0],\n"
            "  [0, cos(\\theta), -i sin(\\theta), 0],\n"
            "  [0, -i sin(\\theta), cos(\\theta), 0],\n"
            "  [0, 0, 0, e^{-i\\phi}]\n"
            "]\n"
            "Donde \\theta representa el ángulo de intercambio de energía (excitación fermiónica) y \\phi "
            "representa la fase de interacción coulombiana."
        )
    }

if __name__ == "__main__":
    print("[QML CORE] Testing autograd model...")
    model = VQCModel(n_qubits=2, layers=1)
    X = np.random.rand(5, 2)
    y = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
    loss = model.train_step(X, y)
    print("[QML CORE] Training loss on 1 step:", loss)
