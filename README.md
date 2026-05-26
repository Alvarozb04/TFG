# Quantum Machine Learning (QML) Sandbox & Portfolio

Este repositorio contiene un **Quantum Machine Learning Sandbox** interactivo y un **Portafolio Profesional** de alto impacto diseñado para demostrar la intersección entre la física cuántica avanzada y la ingeniería de software de alto rendimiento.

El proyecto implementa clasificadores cuánticos variacionales (VQC) y máquinas de vectores de soporte cuánticas (QSVM) utilizando **PennyLane** y **PyTorch** con soporte de aceleración por GPU (**CUDA**). Además, incluye una sección de portafolio técnico dedicada a la simulación cuántica molecular de la **Glicina** empleando transformaciones fermiónicas (**Jordan-Wigner** y **Parity**) y compuertas de simulación fermiónica (**Cfsim**).

---

## 🌌 Fundamentos Físicos y Matemáticos Implementados

### 1. Clasificadores Cuánticos Variacionales (VQC)
Los VQCs representan el análogo cuántico de las Redes Neuronales clásicas. El modelo consta de tres etapas fundamentales:
- **Codificación del Estado (Embedding)**: Mapeo de datos clásicos $x \in \mathbb{R}^d$ a amplitudes o ángulos de un estado cuántico.
  - *Angle Embedding*: Codifica variables continuas como rotaciones unitarias elementales $R_X(\theta_i)$ sobre qubits individuales.
  - *Amplitude Embedding*: Almacena un vector normalizado en las amplitudes de superposición del estado multibody del sistema de qubits. La dimensionalidad del espacio de características crece exponencialmente como $2^N$.
- **Ansatz Variacional (Circuito Parametrizado)**: Aplicación de compuertas unitarias parametrizadas $U(\theta)$ formadas por rotaciones locales y entrelazadores (CNOT o Ising gates). Estos parámetros $\theta$ se entrenan por gradiente clásico.
- **Medición**: Se calcula el valor esperado $\langle \hat{Z} \rangle$ de observables cuánticos (operadores de Pauli-Z) en los qubits de salida, mapeando el estado final a una etiqueta de clase clásica.

### 2. Máquinas de Vectores de Soporte Cuánticas (QSVM)
El método de Kernel Cuántico aprovecha el gran tamaño del espacio de Hilbert cuántico para proyectar datos que no son linealmente separables en dimensiones bajas a un espacio cuántico multidimensional donde se vuelven linealmente separables.
La métrica de similitud o elemento de matriz de Kernel $K(x_i, x_j)$ se calcula directamente como el solapamiento o amplitud de transición de las funciones de onda preparadas:
$$K(x_i, x_j) = |\langle \Phi(x_i) | \Phi(x_j) \rangle|^2$$
Este solapamiento se mide experimentalmente en el simulador cuántico aplicando el mapa de características unitario $U(x_i)$ seguido del adjunto (inverso) del mapa de características del segundo punto $U^\dagger(x_j)$, midiendo finalmente la probabilidad del estado de vacío $|00\dots0\rangle$.

### 3. Simulación de la Molécula de Glicina (TFG Tribute)
El portafolio técnico destaca la simulación cuántica de estructura electrónica de la molécula de Glicina ($C_2H_5NO_2$).
- **Jordan-Wigner vs. Parity Mapping**: Transformaciones que mapean operadores de creación y aniquilación fermiónica ($c_j^\dagger, c_j$) que cumplen anticonmutación fermiónica $\{c_i, c_j^\dagger\} = \delta_{ij}$ en operadores locales de espín/qubits (matrices de Pauli $X, Y, Z$). Jordan-Wigner utiliza cadenas de Pauli-Z para preservar la simetría antisimétrica de los electrones, mientras que Parity Mapping codifica la paridad local reduciendo la cantidad de compuertas de dos qubits necesarias en ciertas topologías.
- **Compuertas Cfsim (Fermionic Simulation)**: Compuertas de dos qubits parametrizadas que conservan el número total de partículas (excitaciones cuánticas). Están definidas en el subespacio $\{|01\rangle, |10\rangle\}$ por un ángulo de intercambio de energía $\theta$ y una fase coulombiana $\phi$ en $|11\rangle$. Esto permite mapear la evolución del Hamiltoniano electrónico molecular de forma óptima en el chip Sycamore de Google u otras arquitecturas NISQ.

---

## 🛠️ Arquitectura de Software

La aplicación está diseñada bajo una estructura desacoplada **Full-Stack de Alto Rendimiento**:
- **Backend asíncrono en FastAPI**: Procesa las solicitudes matemáticas, la generación de datasets no lineales (`make_moons`, `make_circles`) y las peticiones de kernels.
- **Streaming en tiempo real por Server-Sent Events (SSE)**: La ruta `/api/vqc/train` ejecuta el bucle de entrenamiento híbrido PennyLane + PyTorch en un hilo secundario y transmite de forma asíncrona epoch-a-epoch la pérdida, precisión cuántica, métricas clásicas y la matriz de frontera de decisión al navegador.
- **Frontend SPA Ultra-Premium**: Desarrollado con HTML5 semántico, vanilla CSS3 con efectos de desenfoque de fondo (glassmorphism), y Javascript dinámico.
  - **Visualizador Dinámico de Circuitos SVG**: Dibuja el circuito cuántico correspondiente en tiempo real en función de los qubits, capas y ansatz seleccionados, representando las compuertas $R_X, R_Y$, bloques de CNOTs o compuertas fermiónicas.
  - **Canvas de Frontera de Decisión**: Renderiza un mapa de calor dinámico interpolando una malla de predicción de $15\times15$ puntos generada por el backend en cada época de entrenamiento.

---

## 🚀 Instalación y Ejecución Local

Para ejecutar el sandbox interactivo en tu máquina local:

1. **Clonar e ingresar al repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd QML
   ```

2. **Crear e inicializar el entorno virtual de Python**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias necesarias**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Nota: Si cuentas con soporte para GPU NVIDIA, PyTorch detectará automáticamente CUDA para acelerar el procesamiento de PennyLane).*

4. **Iniciar el servidor web**:
   ```bash
   python3 main.py
   ```
   o bien usando Uvicorn directamente:
   ```bash
   uvicorn main:app --reload
   ```

5. **Acceder a la aplicación**:
   Abre tu navegador web e ingresa a `http://localhost:8000`.

---

## 🎯 Demostración de Competencia Técnica (Para Reclutadores)

Este proyecto valida de forma tangible las siguientes competencias clave valoradas por las compañías de computación cuántica:
1. **Modelado Físico y QML**: Dominio de la librería estándar de facto **PennyLane** y algoritmos de optimización de parámetros cuánticos mediante diferenciación automática.
2. **Integración Híbrida**: Habilidad para acoplar QNodes de PennyLane como capas integrables dentro de arquitecturas complejas de Deep Learning en **PyTorch**.
3. **Optimización NISQ**: Conocimiento práctico de los desafíos de hardware NISQ como el decaimiento de gradiente (*barren plateaus*) y reducción del coste de compuertas mediante ansätze específicos (como Cfsim fermiónico).
4. **Desarrollo de Software Industrial**: Capacidad de construir APIs de baja latencia utilizando FastAPI, estructurar códigos orientados a objetos en Python, y crear visualizadores gráficos fluidos con canvas y SVGs.

