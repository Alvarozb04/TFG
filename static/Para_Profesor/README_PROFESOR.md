# Simulación VQE - Comparativa Metodológica (Glicina, 20 Qubits)
**Autor:** Álvaro Zapata Beteta  
**Proyecto:** Trabajo de Fin de Grado (TFG) - Simulación Cuántica de Biomoléculas en HPC

Estimado profesor,

Adjunto en esta carpeta el paquete de software cuántico y configuraciones moleculares listas para ejecutar en el clúster HPC de alto rendimiento.

Con el fin de elevar al máximo el rigor físico e interpretativo del proyecto, he ampliado el flujo de trabajo para plantear una **comparación cruzada de 2x3 (6 casos en total)** que cruza los dos mapeos fermiónicos con tres variantes del circuito cuántico variacional (ansatz):

1. **Mapeos de orbitales a qubits:**
   * **Jordan-Wigner (JW):** Mapeo canónico directo.
   * **Parity Mapping:** Mapeo de paridad acumulada orbital (simetría $Z_2$).
2. **Arquitecturas de Circuito Cuántico (Ansätze):**
   * **cfSim (Circular Estándar):** El ansatz fermiónico circular regular. Utiliza puertas `FSimGate` de intercambio electrónico (`XXPlusYY` + `CPhase`), pero al tener conexiones cerradas en escalera circular, incluye cruces de espín en los enlaces `[9, 10]` y `[19, 0]`.
   * **cfSim (Restringido por Espín - ¡Nuevo!):** Diseñado con **restricciones de simetría molecular estrictas**. Mantiene las puertas `cfSim` de intercambio para transiciones dentro del canal de espín $\alpha$ (qubits 0-9) y $\beta$ (qubits 10-19), pero **desacopla el intercambio de espín en las fronteras** `[9, 10]` y `[19, 0]` sustituyéndolo por puertas **`CPhase` puras** (repulsión electrostática de Coulomb sin intercambio). Esto garantiza la conservación estricta de la proyección del espín ($S_z = 0$, $N_\alpha=5$, $N_\beta=5$), impidiendo fugas cuánticas a estados no físicos.
   * **Normal (HEA):** Grupo de control científico. Un *Hardware-Efficient Ansatz* estándar (rotaciones $R_y, R_z$ y CNOTs circulares). No conserva simetrías físicas de partículas ni espín, pero dispone del **mismo presupuesto de parámetros libres** para una comparación estadística justa.

---

## 📁 Contenido del Paquete

* `vqe_cfsim.py`: Script principal de simulación. Soporta combinaciones vía `--mapper` y `--ansatz`.
* `plot_comparison.py`: Consolidador de resultados. Lee los JSONs de cada corrida y genera gráficos de calidad de revista y reportes Markdown de las simulaciones completadas.
* `active_space.fcidump`: Integrales fermiónicas obtenidas mediante el cálculo clásico en el espacio activo.
* `vqe_input.json`: Configuración física del estado de Hartree-Fock inicial (10 electrones en CAS(10,10)).
* `requirements_hpc.txt`: Dependencias requeridas para la ejecución en nodos HPC (Qiskit 0.45+, Qiskit Nature 0.7+, Numpy, Scipy y Matplotlib).
* `run_hpc.sh`: Script bash automatizado para secuenciar los 6 experimentos y disparar el graficado final.

---

## 🚀 Guía de Ejecución en el Clúster

### Opción 1: Ejecución Automatizada de los 6 Casos (Recomendada)
El script bash secuenciará de manera limpia los 6 experimentos en el clúster. Puedes parametrizar la profundidad (capas) y las iteraciones SPSA como argumentos de consola:

```bash
chmod +x run_hpc.sh

# Formato: ./run_hpc.sh [NÚM_CAPAS] [NÚM_ITERACIONES]
# Ejecución estándar de producción sugerida:
./run_hpc.sh 4 5000
```

> [!TIP]
> **Prueba Rápida de Integridad:** Para verificar en pocos segundos que los scripts compilan y corren en los nodos de cálculo antes de lanzar la simulación pesada, ejecuta:
> ```bash
> ./run_hpc.sh 2 10
> ```

### Opción 2: Ejecución Manual Personalizada
Si deseas aislar una corrida concreta con flags personalizados:

```bash
python3 vqe_cfsim.py --mapper [jordan_wigner|parity] --ansatz [cfsim|cfsim_spin|normal] --layers [capas] --iters [iteraciones] --outdir [carpeta_salida]
```
*Ejemplo:*
```bash
python3 vqe_cfsim.py --mapper jordan_wigner --ansatz cfsim_spin --layers 4 --iters 3000 --outdir vqe_run_jw_cfsim_spin
```

---

## 📊 Entregables y Salidas

Al completarse el flujo automatizado (`./run_hpc.sh`), dispondrás de los siguientes archivos consolidados:
1. **`comparativa_completa_vqe.png`:** Gráfica científica que superpone la convergencia energética de los 6 experimentos (diferenciando mapeos por colores y circuitos por estilos de trazado).
2. **`resumen_comparativo.md`:** Reporte con la tabla de resultados consolidados en formato Markdown y conclusiones físicas de la simulación.
3. **`vqe_run_*/`:** Carpetas de salida por cada caso de estudio con su traza JSON, topología de circuito en texto y su gráfica individual.

¡Muchas gracias por habilitar el soporte de supercomputación para contrastar estas ventajas del modelado cuántico molecular!
