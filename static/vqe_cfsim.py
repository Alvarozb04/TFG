#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
PROYECTO TFG: VQE GEMELO DIGITAL (20 Qubits) - GLICINA
================================================================================
Autor: Álvaro Zapata Beteta
Entorno: HPC / Clúster de Computación
Descripción: Simulación cuántica híbrida comparando Jordan-Wigner y Parity.
================================================================================
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Qiskit imports
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.circuit import ParameterVector, Gate
from qiskit.circuit.library import XXPlusYYGate, CPhaseGate

# Mappers
from qiskit_nature.second_q.mappers import JordanWignerMapper, ParityMapper

try:
    from qiskit_nature.second_q.formats.fcidump import FCIDump
except (ImportError, ModuleNotFoundError):
    from qiskit_nature.second_q.formats import FCIDump

class FSimGate(Gate):
    """Puerta cfSim (FSimGate) para simulación fermiónica."""
    def __init__(self, theta, phi, label=None):
        super().__init__("fsim", 2, [theta, phi], label=label)
    def _define(self):
        qc = QuantumCircuit(2)
        qc.append(XXPlusYYGate(2 * self.params[0], 0), [0, 1])
        qc.append(CPhaseGate(-self.params[1]), [0, 1])
        self.definition = qc

def load_qubit_hamiltonian(fcidump_path: str, mapper_type: str) -> SparsePauliOp:
    if not os.path.exists(fcidump_path):
        raise FileNotFoundError(f"Archivo no encontrado: {fcidump_path}")
    fd = FCIDump.from_file(fcidump_path)
    try:
        from qiskit_nature.second_q.formats import fcidump_to_problem
        problem = fcidump_to_problem(fd)
        ferm_op = problem.hamiltonian.second_q_op()
    except Exception:
        if hasattr(fd, "to_problem"):
            problem = fd.to_problem()
            ferm_op = problem.hamiltonian.second_q_op()
        else:
            raise AttributeError("Error FCIDUMP.")

    if mapper_type == 'jordan_wigner':
        mapper = JordanWignerMapper()
    elif mapper_type == 'parity':
        mapper = ParityMapper()
    else:
        raise ValueError("Mapper no soportado")

    qubit_op = mapper.map(ferm_op)
    if not isinstance(qubit_op, SparsePauliOp):
        qubit_op = SparsePauliOp.from_list(qubit_op.to_list())
    return qubit_op

def convert_hf_bitstring(jw_bitstring: str, mapper_type: str) -> str:
    """Convierte el estado de Hartree-Fock a la base del mapper elegido."""
    if mapper_type == 'jordan_wigner':
        return jw_bitstring
    elif mapper_type == 'parity':
        parity_str = []
        count = 0
        for b in jw_bitstring:
            count = (count + int(b)) % 2
            parity_str.append(str(count))
        return "".join(parity_str)
    return jw_bitstring

def build_cfsim_ansatz(bitstring: str, layers: int = 2):
    n = len(bitstring)
    qc = QuantumCircuit(n, name="cfSim_Ansatz")
    for i, b in enumerate(bitstring):
        if b == "1": qc.x(i)

    n_params = layers * n * 2
    theta_params = ParameterVector("p", n_params)
    k = 0
    for _ in range(layers):
        for q in range(n - 1):
            qc.append(FSimGate(theta_params[k], theta_params[k+1]), [q, q + 1])
            k += 2
        qc.append(FSimGate(theta_params[k], theta_params[k+1]), [n - 1, 0])
        k += 2
    return qc, theta_params

def get_energy(op: SparsePauliOp, qc: QuantumCircuit) -> float:
    psi = Statevector(qc)
    return float(np.real(psi.expectation_value(op)))

def run_spsa_optimization(op, ansatz, theta0, maxiter, a_spsa, c_spsa, stability_a, alpha, gamma):
    nparams = len(theta0)
    theta = theta0.copy()
    energies = []
    t_start = time.time()
    for k in range(1, maxiter + 1):
        ak = a_spsa / ((k + stability_a) ** alpha)
        ck = c_spsa / (k ** gamma)
        delta = 2 * np.random.randint(0, 2, size=nparams) - 1
        e_plus = get_energy(op, ansatz.assign_parameters(theta + ck * delta))
        e_minus = get_energy(op, ansatz.assign_parameters(theta - ck * delta))
        ghat = (e_plus - e_minus) / (2.0 * ck) * delta.astype(float)
        theta = theta - ak * ghat
        e_curr = get_energy(op, ansatz.assign_parameters(theta))
        energies.append(e_curr)
        log_freq = 5 if maxiter <= 500 else 50
        if k % log_freq == 0 or k == 1:
            avg_energy = np.mean(energies[-10:]) if len(energies) > 10 else e_curr
            print(f"    Iter {k:4d}/{maxiter} | E_actual: {e_curr:.8f} Ha | E_avg: {avg_energy:.8f} Ha")
    t_end = time.time()
    print(f"    [OK] SPSA completado en {t_end-t_start:.2f}s")
    return theta, energies

def main():
    parser = argparse.ArgumentParser(description="VQE cfSim Digital Twin (HPC Ready)")
    parser.add_argument('--layers', type=int, default=4, help='Número de capas cfSim')
    parser.add_argument('--iters', type=int, default=1000, help='Iteraciones SPSA')
    parser.add_argument('--outdir', type=str, default='vqe_cfsim_out', help='Carpeta de salida')
    args = parser.parse_args()

    header = " VQE WORKFLOW: JORDAN-WIGNER vs PARITY "
    print("\n" + "="*70 + "\n" + header.center(70) + "\n" + "="*70)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUT_DIR = os.path.join(BASE_DIR, args.outdir)
    os.makedirs(OUT_DIR, exist_ok=True)
    
    FCIDUMP_FILE = os.path.join(BASE_DIR, "active_space.fcidump")
    VQE_INPUT_FILE = os.path.join(BASE_DIR, "vqe_input.json")

    with open(VQE_INPUT_FILE, "r") as f:
        vqe_data = json.load(f)
        hf_bitstring_jw = vqe_data["hf"]["bitstring_alpha_beta"]
    
    # --------------------------------------------------------------------------
    # BLOQUE 1: JORDAN-WIGNER
    # --------------------------------------------------------------------------
    print("\n[MÉTODO 1] Mapeo Jordan-Wigner...")
    hamiltonian_jw = load_qubit_hamiltonian(FCIDUMP_FILE, 'jordan_wigner')
    ansatz_jw, params_jw = build_cfsim_ansatz(hf_bitstring_jw, layers=args.layers)
    
    np.random.seed(7)
    theta_init_jw = np.random.uniform(-0.1, 0.1, size=len(params_jw))
    
    print(">>> Iniciando Optimización Jordan-Wigner")
    _, history_jw = run_spsa_optimization(hamiltonian_jw, ansatz_jw, theta_init_jw, args.iters, 0.1, 0.1, 50, 0.602, 0.101)
    
    # --------------------------------------------------------------------------
    # BLOQUE 2: PARITY
    # --------------------------------------------------------------------------
    print("\n[MÉTODO 2] Mapeo Parity...")
    hf_bitstring_parity = convert_hf_bitstring(hf_bitstring_jw, 'parity')
    print(f"    - Estado HF Original (JW) : {hf_bitstring_jw}")
    print(f"    - Estado HF Parity        : {hf_bitstring_parity}")
    
    hamiltonian_parity = load_qubit_hamiltonian(FCIDUMP_FILE, 'parity')
    ansatz_parity, params_parity = build_cfsim_ansatz(hf_bitstring_parity, layers=args.layers)
    
    np.random.seed(7)
    theta_init_parity = np.random.uniform(-0.1, 0.1, size=len(params_parity))
    
    print(">>> Iniciando Optimización Parity")
    _, history_parity = run_spsa_optimization(hamiltonian_parity, ansatz_parity, theta_init_parity, args.iters, 0.1, 0.1, 50, 0.602, 0.101)

    # --------------------------------------------------------------------------
    # C. RESULTADOS Y COMPARATIVA
    # --------------------------------------------------------------------------
    e_core = -258.3179
    e_total_jw = history_jw[-1] + e_core
    e_total_parity = history_parity[-1] + e_core

    print("\n" + "="*70)
    print(" RESULTADOS COMPARATIVOS ".center(70))
    print("="*70)
    print(f" Energía Jordan-Wigner : {e_total_jw:.10f} Ha")
    print(f" Energía Parity        : {e_total_parity:.10f} Ha")
    print("="*70)

    # Guardar gráfico comparativo
    plt.figure(figsize=(10, 6))
    plt.plot(history_jw, color='#1f77b4', linewidth=2, label='Jordan-Wigner')
    plt.plot(history_parity, color='#ff7f0e', linewidth=2, linestyle='--', label='Parity')
    plt.title(f"Comparativa Convergencia VQE (Glicina - {ansatz_jw.num_qubits} Qubits | {args.layers} Capas)")
    plt.xlabel("Iteraciones SPSA")
    plt.ylabel("Energía Activa (Ha)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(OUT_DIR, "convergencia_comparativa.png"), dpi=200)
    
    with open(os.path.join(OUT_DIR, "circuito_ansatz.txt"), "w") as f:
        f.write(ansatz_jw.draw(output='text').single_string())

    print(f"\n[+] Resultados e imagen guardados en: {OUT_DIR}/")
    print(">>> PROCESO COMPLETADO CON ÉXITO <<<\n")

if __name__ == "__main__":
    main()
