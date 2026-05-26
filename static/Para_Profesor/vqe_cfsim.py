#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
PROYECTO TFG: VQE GEMELO DIGITAL (20 Qubits) - GLICINA
================================================================================
Autor: Álvaro Zapata Beteta
Entorno: HPC / Clúster de Computación
Descripción: Simulación de química cuántica unificada.
             Soporta mapeos Jordan-Wigner y Parity.
             Compara circuitos cuánticos cfSim (Circular), cfSim (Restringido por Espín)
             y Normal (HEA).
             Diseñado para ejecución paralela en CPU de alto rendimiento.
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

# Manejo de FCIDump para diferentes versiones de Qiskit Nature
try:
    from qiskit_nature.second_q.formats.fcidump import FCIDump
except (ImportError, ModuleNotFoundError):
    from qiskit_nature.second_q.formats import FCIDump

# ==============================================================================
# 1. DEFINICIÓN DE PUERTAS CUÁNTICAS (cfSim)
# ==============================================================================
class FSimGate(Gate):
    """
    Implementación personalizada de la puerta cfSim (FSimGate).
    Combina XXPlusYY (iSWAP parcial) y CPhase. Conservadora de número de partículas.
    """
    def __init__(self, theta, phi, label=None):
        super().__init__("fsim", 2, [theta, phi], label=label)
        
    def _define(self):
        qc = QuantumCircuit(2)
        qc.append(XXPlusYYGate(2 * self.params[0], 0), [0, 1])
        qc.append(CPhaseGate(-self.params[1]), [0, 1])
        self.definition = qc

# ==============================================================================
# 2. CONVERSIÓN DE BITSTRINGS DE HARTREE-FOCK
# ==============================================================================
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

# ==============================================================================
# 3. NÚCLEO DEL PROBLEMA (Hamiltoniano y Ansatz)
# ==============================================================================
def load_qubit_hamiltonian(fcidump_path: str, mapper_type: str) -> SparsePauliOp:
    """Carga las integrales de FCIDump y las mapea a qubits usando el mapper elegido."""
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
            raise AttributeError("Error al procesar FCIDUMP. Revisa la versión de qiskit-nature.")

    # Selección del mapper
    if mapper_type == 'jordan_wigner':
        mapper = JordanWignerMapper()
    elif mapper_type == 'parity':
        mapper = ParityMapper()
    else:
        raise ValueError(f"Mapper '{mapper_type}' no soportado. Elija 'jordan_wigner' o 'parity'.")

    qubit_op = mapper.map(ferm_op)

    if not isinstance(qubit_op, SparsePauliOp):
        qubit_op = SparsePauliOp.from_list(qubit_op.to_list())
    return qubit_op

def build_cfsim_ansatz(bitstring: str, layers: int = 2):
    """Construye el ansatz del Gemelo Digital usando puertas físicas cfSim estándares (escalera circular)."""
    n = len(bitstring)
    qc = QuantumCircuit(n, name="cfSim_Ansatz")
    
    # Estado inicial Hartree-Fock en base computacional
    for i, b in enumerate(bitstring):
        if b == "1": qc.x(i)

    # Parámetros: 2 por cada par entrelazado (theta, phi) en cada capa
    n_params = layers * n * 2
    theta_params = ParameterVector("p", n_params)

    k = 0
    for _ in range(layers):
        # Entrelazamiento lineal (escalera)
        for q in range(n - 1):
            qc.append(FSimGate(theta_params[k], theta_params[k+1]), [q, q + 1])
            k += 2
        # Cierre del anillo (circular)
        qc.append(FSimGate(theta_params[k], theta_params[k+1]), [n - 1, 0])
        k += 2

    return qc, theta_params

def build_cfsim_spin_ansatz(bitstring: str, layers: int = 2):
    """
    Construye el ansatz cfSim RESTINGIDO POR ESPÍN.
    - Los qubits 0-9 (bloque alpha) y 10-19 (bloque beta) se entrelazan internamente con FSimGate (XXPlusYY + CPhase).
    - Los cruces de espín ([9, 10] y [19, 0]) solo se acoplan mediante CPhaseGate (repulsión de Coulomb),
      prohibiendo el intercambio de partículas y conservando estrictamente el espín Sz = 0 de la molécula.
    """
    n = len(bitstring)
    qc = QuantumCircuit(n, name="cfSim_Spin_Ansatz")
    
    # Estado inicial Hartree-Fock en base computacional
    for i, b in enumerate(bitstring):
        if b == "1": qc.x(i)

    # Conexiones intra-espín (18 por capa, 2 parámetros c/u) + inter-espín (2 por capa, 1 parámetro c/u)
    # Total de parámetros por capa = 18 * 2 + 2 * 1 = 38 parámetros.
    n_params = layers * 38
    theta_params = ParameterVector("p", n_params)

    k = 0
    for _ in range(layers):
        # Conexiones lineales
        for q in range(n - 1):
            if q == 9:
                # Cruce de espín: aplicamos únicamente CPhase ( Coulomb ) para evitar saltos
                qc.append(CPhaseGate(-theta_params[k]), [q, q + 1])
                k += 1
            else:
                # Conexión regular intra-espín: cfSim completo (XXPlusYY + CPhase)
                qc.append(FSimGate(theta_params[k], theta_params[k+1]), [q, q + 1])
                k += 2
        # Cierre circular (cruce de espín [19, 0]): aplicamos únicamente CPhase
        qc.append(CPhaseGate(-theta_params[k]), [n - 1, 0])
        k += 1

    return qc, theta_params

def build_normal_ansatz(bitstring: str, layers: int = 2):
    """
    Construye un Hardware-Efficient Ansatz (HEA) estándar usando Ry, Rz y CNOTs.
    No conserva el número de partículas.
    Tiene exactamente el mismo número de parámetros libres que el ansatz cfSim estándar para una comparación justa.
    """
    n = len(bitstring)
    qc = QuantumCircuit(n, name="Normal_Ansatz")
    
    # Estado inicial Hartree-Fock en base computacional
    for i, b in enumerate(bitstring):
        if b == "1": qc.x(i)

    # Parámetros: 2 por cada qubit en cada capa (theta para Ry, phi para Rz)
    # Total de parámetros: layers * n * 2. Idéntico a cfSim estándar!
    n_params = layers * n * 2
    theta_params = ParameterVector("p", n_params)

    k = 0
    for _ in range(layers):
        # Rotaciones parametrizadas en cada qubit
        for i in range(n):
            qc.ry(theta_params[k], i)
            qc.rz(theta_params[k+1], i)
            k += 2
        # Entrelazamiento circular (CNOTs) equivalente a la conectividad de cfSim
        for q in range(n - 1):
            qc.cx(q, q + 1)
        qc.cx(n - 1, 0)

    return qc, theta_params

def get_energy(op: SparsePauliOp, qc: QuantumCircuit) -> float:
    """Calcula el valor esperado de la energía usando Statevector."""
    # En máquinas HPC, Statevector se paralela automáticamente vía OMP_NUM_THREADS
    psi = Statevector(qc)
    return float(np.real(psi.expectation_value(op)))

# ==============================================================================
# 4. MOTOR DE OPTIMIZACIÓN SPSA
# ==============================================================================
def run_spsa_optimization(op, ansatz, theta0, maxiter, a_spsa, c_spsa, stability_a, alpha, gamma):
    """Optimización SPSA pura adaptada para ejecución masiva en clústeres."""
    print(f"\n>>> INICIANDO OPTIMIZACIÓN SPSA ({maxiter} iteraciones)...")
    
    nparams = len(theta0)
    theta = theta0.copy()
    energies = []
    
    t_start = time.time()
    for k in range(1, maxiter + 1):
        # Programación de coeficientes SPSA estándar
        ak = a_spsa / ((k + stability_a) ** alpha)
        ck = c_spsa / (k ** gamma)

        # Perturbación estocástica de Bernoulli (+1 o -1)
        delta = 2 * np.random.randint(0, 2, size=nparams) - 1
        
        # Evaluaciones gemelas (+/- perturbation)
        e_plus = get_energy(op, ansatz.assign_parameters(theta + ck * delta))
        e_minus = get_energy(op, ansatz.assign_parameters(theta - ck * delta))

        # Estimación del gradiente estocástico
        ghat = (e_plus - e_minus) / (2.0 * ck) * delta.astype(float)
        
        # Actualización de parámetros
        theta = theta - ak * ghat
        
        # Guardar energía del estado actual
        e_curr = get_energy(op, ansatz.assign_parameters(theta))
        energies.append(e_curr)

        # Frecuencia de logs en terminal
        log_freq = 5 if maxiter <= 100 else (50 if maxiter <= 1000 else 100)
        if k % log_freq == 0 or k == 1:
            avg_energy = np.mean(energies[-10:]) if len(energies) > 10 else e_curr
            print(f"    Iter {k:4d}/{maxiter} | E_actual: {e_curr:.8f} Ha | E_avg: {avg_energy:.8f} Ha")

    t_end = time.time()
    elapsed_time = t_end - t_start
    print(f"    [OK] SPSA completado en {elapsed_time:.2f}s")
    return theta, energies, elapsed_time

# ==============================================================================
# 5. FLUJO DE TRABAJO PRINCIPAL
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="VQE cfSim/Normal Digital Twin (HPC Ready) - Glicina")
    parser.add_argument('--mapper', type=str, default='jordan_wigner', choices=['jordan_wigner', 'parity'],
                        help='Mapeo fermiónico (jordan_wigner o parity)')
    parser.add_argument('--ansatz', type=str, default='cfsim', choices=['cfsim', 'cfsim_spin', 'normal'],
                        help='Arquitectura del circuito (cfsim: circular estándar, cfsim_spin: restringido por espín, normal: HEA)')
    parser.add_argument('--layers', type=int, default=4, help='Número de capas del ansatz (default: 4)')
    parser.add_argument('--iters', type=int, default=1000, help='Iteraciones del optimizador SPSA (default: 1000)')
    parser.add_argument('--outdir', type=str, default='vqe_output', help='Carpeta de salida para resultados')
    args = parser.parse_args()

    # Formatear el encabezado
    header = f" VQE WORKFLOW: {args.mapper.upper()} + {args.ansatz.upper()} "
    print("\n" + "="*70 + "\n" + header.center(70) + "\n" + "="*70)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUT_DIR = os.path.join(BASE_DIR, args.outdir)
    os.makedirs(OUT_DIR, exist_ok=True)
    
    FCIDUMP_FILE = os.path.join(BASE_DIR, "active_space.fcidump")
    VQE_INPUT_FILE = os.path.join(BASE_DIR, "vqe_input.json")

    # A. Carga de configuración Hartree-Fock
    print("[+] Cargando configuración de la glicina...")
    with open(VQE_INPUT_FILE, "r") as f:
        vqe_data = json.load(f)
        hf_bitstring_jw = vqe_data["hf"]["bitstring_alpha_beta"]
    
    # Adaptar estado Hartree-Fock según el mapeo seleccionado
    hf_bitstring = convert_hf_bitstring(hf_bitstring_jw, args.mapper)
    print(f"    - Mapeo seleccionado : {args.mapper}")
    print(f"    - Estado HF (JW)     : {hf_bitstring_jw}")
    print(f"    - Estado HF Adaptado : {hf_bitstring}")

    # B. Cargar Hamiltoniano cuántico mapeado
    print("[+] Mapeando Hamiltoniano fermiónico a operadores de qubit...")
    hamiltonian = load_qubit_hamiltonian(FCIDUMP_FILE, args.mapper)
    
    # C. Construir el circuito (ansatz) seleccionado
    print(f"[+] Construyendo circuito ansatz: {args.ansatz}")
    if args.ansatz == 'cfsim':
        ansatz, params = build_cfsim_ansatz(hf_bitstring, layers=args.layers)
    elif args.ansatz == 'cfsim_spin':
        ansatz, params = build_cfsim_spin_ansatz(hf_bitstring, layers=args.layers)
    else:
        ansatz, params = build_normal_ansatz(hf_bitstring, layers=args.layers)

    print(f"    - Número de Qubits   : {ansatz.num_qubits}")
    print(f"    - Capas del Ansatz   : {args.layers}")
    print(f"    - Parámetros Libres  : {len(params)}")
    
    # D. Optimización SPSA
    np.random.seed(7)  # Para reproducibilidad matemática
    theta_init = np.random.uniform(-0.1, 0.1, size=len(params))
    
    theta_final, history, elapsed = run_spsa_optimization(
        op=hamiltonian, 
        ansatz=ansatz, 
        theta0=theta_init,
        maxiter=args.iters,
        a_spsa=0.1,
        c_spsa=0.1,
        stability_a=50,
        alpha=0.602,
        gamma=0.101
    )

    # E. Resultados
    e_final = history[-1]
    e_core = -258.3179  # Energía constante del core
    e_total = e_final + e_core

    print("\n" + "="*70)
    print(" RESULTADOS PARCIALES ".center(70))
    print("="*70)
    print(f" Energía Activa (Final)  : {e_final:.10f} Ha")
    print(f" Energía Total (Molécula): {e_total:.10f} Ha")
    print(f" Tiempo transcurrido     : {elapsed:.2f} s")
    print("="*70)

    # F. Guardar resultados y metadatos
    print("\n[+] Guardando resultados y gráfico de convergencia...")
    
    # Guardar gráfico individual
    plt.figure(figsize=(10, 6))
    plt.plot(history, color='#2ca02c' if 'cfsim' in args.ansatz else '#d62728', linewidth=2, label='Convergencia SPSA')
    plt.axhline(y=e_final, color='black', linestyle='--', alpha=0.5, label=f"Final: {e_final:.6f} Ha")
    plt.title(f"Convergencia VQE ({args.mapper.upper()} + {args.ansatz.upper()} | {args.layers} Capas)")
    plt.xlabel("Iteraciones SPSA")
    plt.ylabel("Energía Activa (Ha)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(OUT_DIR, "convergencia_individual.png"), dpi=200)
    plt.close()
    
    # Dibujar topología en texto
    with open(os.path.join(OUT_DIR, "circuito_ansatz.txt"), "w") as f:
        f.write(ansatz.draw(output='text').single_string())
        
    # Guardar datos en formato JSON legible para plot_comparison.py
    results_data = {
        "mapper": args.mapper,
        "ansatz": args.ansatz,
        "layers": args.layers,
        "iters": args.iters,
        "num_qubits": ansatz.num_qubits,
        "num_parameters": len(params),
        "active_energy_history": history,
        "final_active_energy": e_final,
        "final_total_energy": e_total,
        "elapsed_seconds": elapsed,
        "e_core": e_core
    }
    
    with open(os.path.join(OUT_DIR, "vqe_results.json"), "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"[+] Simulación finalizada con éxito. Datos guardados en: {OUT_DIR}/\n")

if __name__ == "__main__":
    main()
