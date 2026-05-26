#!/bin/bash

# ==============================================================================
# SCRIPT DE AUTOMATIZACIÓN HPC: COMPARATIVA VQE - GLICINA (20 QUBITS)
# ==============================================================================
# Autor: Álvaro Zapata Beteta
# Uso: ./run_hpc.sh [capas] [iteraciones]
# Ejemplo: ./run_hpc.sh 4 2000
# ==============================================================================

# Valores por defecto si no se pasan argumentos
LAYERS=${1:-4}
ITERS=${2:-2000}

echo "=========================================================="
echo "    EJECUCIÓN HPC AUTOMATIZADA: VQE GLICINA (20 QUBITS)   "
echo "    Autor: Álvaro Zapata Beteta                             "
echo "=========================================================="
echo "    Configuración actual:"
echo "    - Capas del Ansatz   : $LAYERS"
echo "    - Iteraciones SPSA   : $ITERS"
echo "=========================================================="
echo ""

# 1. Asegurar la instalación de dependencias en el clúster
echo "[1/8] Verificando dependencias en el entorno HPC..."
pip install -r requirements_hpc.txt -q
if [ $? -eq 0 ]; then
    echo "    [OK] Dependencias listas."
else
    echo "    [ADVERTENCIA] Error al instalar dependencias con pip. Continuando con las instaladas..."
fi

# 2. CASO 1: Jordan-Wigner + cfSim (Circular)
echo ""
echo "[2/8] Lanzando CASO 1: Jordan-Wigner + cfSim (Circular)..."
echo "    Guardando en: vqe_run_jw_cfsim/"
python3 vqe_cfsim.py --mapper jordan_wigner --ansatz cfsim --layers $LAYERS --iters $ITERS --outdir vqe_run_jw_cfsim

# 3. CASO 2: Jordan-Wigner + cfSim (Restringido por Espín)
echo ""
echo "[3/8] Lanzando CASO 2: Jordan-Wigner + cfSim (Restringido por Espín)..."
echo "    Guardando en: vqe_run_jw_cfsim_spin/"
python3 vqe_cfsim.py --mapper jordan_wigner --ansatz cfsim_spin --layers $LAYERS --iters $ITERS --outdir vqe_run_jw_cfsim_spin

# 4. CASO 3: Jordan-Wigner + Normal (HEA)
echo ""
echo "[4/8] Lanzando CASO 3: Jordan-Wigner + Normal (HEA)..."
echo "    Guardando en: vqe_run_jw_normal/"
python3 vqe_cfsim.py --mapper jordan_wigner --ansatz normal --layers $LAYERS --iters $ITERS --outdir vqe_run_jw_normal

# 5. CASO 4: Parity + cfSim (Circular)
echo ""
echo "[5/8] Lanzando CASO 4: Parity + cfSim (Circular)..."
echo "    Guardando en: vqe_run_parity_cfsim/"
python3 vqe_cfsim.py --mapper parity --ansatz cfsim --layers $LAYERS --iters $ITERS --outdir vqe_run_parity_cfsim

# 6. CASO 5: Parity + cfSim (Restringido por Espín)
echo ""
echo "[6/8] Lanzando CASO 5: Parity + cfSim (Restringido por Espín)..."
echo "    Guardando en: vqe_run_parity_cfsim_spin/"
python3 vqe_cfsim.py --mapper parity --ansatz cfsim_spin --layers $LAYERS --iters $ITERS --outdir vqe_run_parity_cfsim_spin

# 7. CASO 6: Parity + Normal (HEA)
echo ""
echo "[7/8] Lanzando CASO 6: Parity + Normal (HEA)..."
echo "    Guardando en: vqe_run_parity_normal/"
python3 vqe_cfsim.py --mapper parity --ansatz normal --layers $LAYERS --iters $ITERS --outdir vqe_run_parity_normal

# 8. Ejecutar script de análisis y graficado comparativo
echo ""
echo "[8/8] Consolidando resultados y generando reporte/gráficas..."
python3 plot_comparison.py

echo ""
echo "=========================================================="
echo " [OK] TODAS LAS SIMULACIONES HAN FINALIZADO CON ÉXITO."
echo " Resultados listos en:"
echo " - Gráfico: comparativa_completa_vqe.png"
echo " - Reporte: resumen_comparativo.md"
echo " - Carpetas individuales: vqe_run_*"
echo "=========================================================="
