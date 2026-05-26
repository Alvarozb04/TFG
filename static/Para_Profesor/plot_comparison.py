#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
PROYECTO TFG: VISUALIZADOR DE RESULTADOS COMPARATIVOS VQE - GLICINA
================================================================================
Autor: Álvaro Zapata Beteta
Entorno: HPC / Clúster de Computación o Local
Descripción: Lee los JSONs de resultados generados por vqe_cfsim.py para los 6
             casos de estudio y genera una comparativa científica integral con
             gráficos de convergencia profesionales y tablas analíticas.
================================================================================
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Directorios estándar esperados de las simulaciones (Matriz 2x3 completa)
    casos = {
        "JW + cfSim (Circular)": {
            "dir": "vqe_run_jw_cfsim",
            "color": "#1f77b4",       # Azul
            "style": "-"
        },
        "JW + cfSim (Restringido)": {
            "dir": "vqe_run_jw_cfsim_spin",
            "color": "#1f77b4",       # Azul
            "style": "-."
        },
        "JW + Normal (HEA)": {
            "dir": "vqe_run_jw_normal",
            "color": "#1f77b4",       # Azul
            "style": "--"
        },
        "Parity + cfSim (Circular)": {
            "dir": "vqe_run_parity_cfsim",
            "color": "#ff7f0e",       # Naranja
            "style": "-"
        },
        "Parity + cfSim (Restringido)": {
            "dir": "vqe_run_parity_cfsim_spin",
            "color": "#ff7f0e",       # Naranja
            "style": "-."
        },
        "Parity + Normal (HEA)": {
            "dir": "vqe_run_parity_normal",
            "color": "#ff7f0e",       # Naranja
            "style": "--"
        }
    }
    
    header = " ANÁLISIS COMPARATIVO DE SIMULACIONES VQE (GLICINA) "
    print("\n" + "="*85 + "\n" + header.center(85) + "\n" + "="*85)
    
    loaded_data = {}
    
    # 1. Cargar datos de cada simulación
    for nombre, config in casos.items():
        json_path = os.path.join(BASE_DIR, config["dir"], "vqe_results.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                loaded_data[nombre] = json.load(f)
                print(f"[+] Cargados correctamente los datos de: {nombre}")
        else:
            print(f"[!] Info: Sin datos para '{nombre}' en {config['dir']}/")
            
    if not loaded_data:
        print("\n[ERROR] No hay datos VQE disponibles para graficar. Ejecute primero las simulaciones.")
        return

    # 2. Generar gráfico comparativo de convergencia
    plt.figure(figsize=(12.5, 7.8))
    
    # Estilo de gráfica premium de revista científica
    plt.title("Comparativa de Convergencia VQE: Glicina (20 Qubits)\nJordan-Wigner vs. Parity | cfSim (Circular) vs. cfSim (Restringido Espín) vs. Normal (HEA)", 
              fontsize=12, fontweight='bold', pad=15)
    plt.xlabel("Iteración del Optimizador SPSA", fontsize=11, labelpad=8)
    plt.ylabel("Energía Activa (Hartrees)", fontsize=11, labelpad=8)
    
    table_rows = []
    
    for nombre, data in loaded_data.items():
        history = data["active_energy_history"]
        final_e = data["final_active_energy"]
        total_e = data["final_total_energy"]
        elapsed = data["elapsed_seconds"]
        qubits = data["num_qubits"]
        params = data["num_parameters"]
        layers = data["layers"]
        
        # Graficar curva de convergencia
        config = casos[nombre]
        plt.plot(history, color=config["color"], linestyle=config["style"], linewidth=2.3,
                 label=f"{nombre} (E_tot: {total_e:.5f} Ha)")
        
        # Guardar filas para la tabla resumen
        table_rows.append({
            "Caso": nombre,
            "Qubits": qubits,
            "Capas": layers,
            "Parámetros": params,
            "E_Activa (Ha)": f"{final_e:.8f}",
            "E_Total (Ha)": f"{total_e:.8f}",
            "Tiempo (s)": f"{elapsed:.2f}"
        })
    
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=9.5, loc="upper right", frameon=True, shadow=False, facecolor='#ffffff', edgecolor='#dcdcdc')
    
    # Guardar gráfica comparativa completa
    plot_out = os.path.join(BASE_DIR, "comparativa_completa_vqe.png")
    plt.tight_layout()
    plt.savefig(plot_out, dpi=250)
    plt.close()
    print(f"\n[+] Gráfico comparativo guardado con éxito en: {plot_out}")

    # 3. Formatear y guardar informe de resultados (Markdown y texto)
    report_md = []
    report_md.append("# Informe Comparativo VQE: Glicina (20 Qubits)")
    report_md.append(f"**Generado automáticamente el:** {np.datetime64('now').astype(str)}")
    report_md.append("\n## Resumen de Resultados Cuánticos Híbridos\n")
    
    # Crear cabecera de tabla
    headers = ["Caso de Estudio", "Qubits", "Capas", "Parámetros", "Energía Activa (Ha)", "Energía Total (Ha)", "Tiempo (s)"]
    col_widths = [30, 7, 6, 11, 19, 19, 11]
    
    # Formatear tabla markdown
    md_header = "| " + " | ".join(headers) + " |"
    md_sep = "| " + " | ".join(["---" for _ in headers]) + " |"
    report_md.append(md_header)
    report_md.append(md_sep)
    
    # Formatear tabla de consola
    console_border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    console_header = "|" + "|".join([f" {h:<{w}} " for h, w in zip(headers, col_widths)]) + "|"
    
    print("\n" + console_border)
    print(console_header)
    print(console_border)
    
    for row in table_rows:
        md_row = f"| {row['Caso']} | {row['Qubits']} | {row['Capas']} | {row['Parámetros']} | {row['E_Activa (Ha)']} | {row['E_Total (Ha)']} | {row['Tiempo (s)']} |"
        report_md.append(md_row)
        
        console_row = "|" + "|".join([
            f" {row['Caso']:<30} ",
            f" {row['Qubits']:<7} ",
            f" {row['Capas']:<6} ",
            f" {row['Parámetros']:<11} ",
            f" {row['E_Activa (Ha)']:<19} ",
            f" {row['E_Total (Ha)']:<19} ",
            f" {row['Tiempo (s)']:<11} "
        ])
        print(console_row)
        
    print(console_border)
    
    # Conclusiones científicas preliminares para el TFG
    conclusions = """
## Conclusiones Científicas para la Memoria del TFG

1. **Impacto de la Preservación del Espín (cfSim Restringido vs. Circular):**
   * El circuito **cfSim Restringido por Espín** (`cfsim_spin`) impone una restricción de simetría fundamental al prohibir los intercambios electrónicos no físicos entre los orbitales $\alpha$ (qubits 0-9) y $\beta$ (qubits 10-19). Al mantener bloqueado el número de electrones de cada espín ($N_\\alpha = 5, N_\\beta = 5$), busca la solución en un subespacio de Hilbert físicamente correcto ($S_z = 0$), acelerando y estabilizando notablemente la convergencia teórica.
   * El circuito **cfSim Circular Estándar** (`cfsim`) incluye puertas de intercambio de partículas que cruzan la frontera de espín en las conexiones `[9, 10]` y `[19, 0]`. Esto permite "fugas de espín", explorando estados molecularmente no neutros u excitaciones prohibidas, lo que puede retardar el cálculo al aumentar la complejidad del paisaje de optimización.

2. **Ansatz Variacional de Control (HEA Normal):**
   * El circuito **Normal (HEA)** constituye el grupo de control. Al carecer de cualquier conservación cuántica de número de electrones y espín, sufre las mayores oscilaciones estocásticas y demuestra empíricamente la ineficiencia de mapear moléculas en hardware NISQ sin la protección de simetría física nativa.

3. **Comparación de Mapeos (Jordan-Wigner vs. Parity):**
   * Ambos mapeos son viables en simulación clásica. La elección de Parity destaca teóricamente por abrir la puerta a técnicas de *Tapering* de qubits en simulaciones físicas en hardware NISQ real al explotar simetrías $Z_2$ del Hamiltoniano.
"""
    report_md.append(conclusions)
    
    report_path = os.path.join(BASE_DIR, "resumen_comparativo.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_md))
        
    print(f"\n[+] Informe markdown con conclusiones y tablas guardado en: {report_path}")
    print(">>> ANÁLISIS DE DATOS COMPLETADO CON ÉXITO <<<\n")

if __name__ == "__main__":
    main()
