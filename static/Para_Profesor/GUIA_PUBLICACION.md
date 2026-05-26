# Guía de Publicación y Despliegue del Portafolio Q-ML
**Autor:** Álvaro Zapata Beteta  
**Proyecto:** Trabajo de Fin de Grado (TFG) - Visualizador Digital Twin de Glicina & Sandbox Q-ML

Para compartir este portafolio interactivo con tu tutor de una forma profesional, tienes dos opciones principales según lo que desees que examine en vivo:

---

## 🌐 Opción A: Despliegue Estático (Recomendado para el Visualizador 3D)
**¿Qué se publica?** El visualizador 3D interactivo (`glicina_interactiva.html`), tu portafolio/CV (`index.html`), las hojas de estilo y los scripts del cliente.  
**Ventaja:** Es 100% gratuito, ultra rápido y no requiere servidores activos, ya que los gráficos 3D (Three.js), las animaciones de orbitales (GSAP) y el simulador de desprotonación se ejecutan directamente en el navegador del tutor.

### Método 1: GitHub Pages (El más profesional)
GitHub Pages te permite alojar páginas directamente desde un repositorio de código.
1. Crea una cuenta en [GitHub](https://github.com/) si aún no tienes una.
2. Sube los archivos de la carpeta `static/` (o todo tu repositorio) a un repositorio público en tu perfil de GitHub (por ejemplo, llámalo `QML-Portfolio`).
3. En GitHub, ve a **Settings** (Configuración de tu repositorio) > **Pages** (en la barra lateral).
4. Bajo **Build and deployment**, selecciona la rama `main` (o `master`) y la carpeta `/root` (o `/docs` si moviste los archivos estáticos allí) y haz clic en **Save**.
5. ¡Listo! En un par de minutos tu proyecto estará visible en:  
   `https://<tu-usuario-github>.github.io/QML-Portfolio/index.html` (o `glicina_interactiva.html` para ir directo al 3D).

### Método 2: Vercel / Netlify (El más rápido sin código)
Vercel y Netlify son plataformas premium de despliegue con un método "drag-and-drop" (arrastrar y soltar) muy rápido.
1. Entra en [Vercel](https://vercel.com/) o [Netlify](https://www.netlify.com/) y crea una cuenta gratuita.
2. Comprime tu carpeta `static/` en un archivo `.zip` (o arrastra la carpeta directamente).
3. En el panel de control de Vercel/Netlify, suelta el archivo zip en el área de despliegue instantáneo.
4. La plataforma compilará el sitio en segundos y te dará una URL premium segura (HTTPS) para compartir con tu tutor.

---

## ⚡ Opción B: Despliegue Full-Stack (Para correr el Sandbox de Q-ML activo)
**¿Qué se publica?** Todo el proyecto, incluyendo el servidor backend en Python con FastAPI (`main.py`), los modelos cuánticos (`qml_models.py`) y clásicos.  
**Ventaja:** Permite que tu tutor ejecute los bucles de entrenamiento variacional cuántico (VQC) y calcule las matrices del kernel QSVM en tiempo real en la web.

### Método: Render.com (Servidor de Aplicaciones Gratuito/Bajo costo)
Render permite alojar servicios web Python de forma muy directa y gratuita.
1. Crea una cuenta en [Render.com](https://render.com/).
2. Sube todo tu código (incluyendo `main.py`, `static/`, `requirements.txt`, etc.) a un repositorio en tu cuenta de GitHub.
3. En el panel de Render, haz clic en **New +** y selecciona **Web Service**.
4. Conecta tu cuenta de GitHub y selecciona el repositorio de tu proyecto.
5. Configura los parámetros del servicio:
   * **Runtime:** `Python`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. En la pestaña **Environment**, asegúrate de que no haya variables complejas de GPU.
7. Haz clic en **Create Web Service**.
8. Render instalará los paquetes y levantará tu servidor FastAPI automáticamente. Te proporcionará una URL pública tipo `https://qml-portfolio.onrender.com`.

---

## 🎯 Recomendación Estratégica para tu TFG
Para tu tutor, lo más impactante a nivel visual es el **Gemelo Digital 3D de la Glicina**. 

Te sugerimos desplegar **la Opción A en GitHub Pages**. Esto demuestra habilidades de control de versiones y hosting profesional. En tu portafolio, el tutor podrá interactuar con la molécula, ver los orbitales moleculares y disparar el simulador de protones sin latencia alguna. 

¡Si necesitas cualquier archivo de configuración adicional (como un archivo de despliegue de GitHub Actions o Dockerfile), dímelo y lo prepararemos de inmediato!
