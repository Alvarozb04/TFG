#!/bin/bash
# Script para subir el portafolio del TFG de Álvaro a GitHub

# 1. Comprobar si git está instalado
if ! command -v git &> /dev/null
then
    echo "⚠️ Git no está instalado en tu sistema Fedora. Intentando instalarlo..."
    echo "Por favor, introduce tu contraseña de administrador (sudo) si se te solicita:"
    sudo dnf install -y git
    if [ $? -ne 0 ]; then
        echo "❌ No se pudo instalar Git automáticamente. Por favor, instálalo manualmente con: sudo dnf install git"
        exit 1
    fi
fi

# 2. Inicializar repositorio si no está ya inicializado
if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
fi

# 3. Crear .gitignore para evitar subir la carpeta venv/ y temporales pesados
if [ ! -f .gitignore ]; then
    echo "Creando archivo .gitignore..."
    cat <<EOT >> .gitignore
venv/
.venv/
__pycache__/
*.pyc
.gemini/
.system_generated/
*.log
EOT
fi

# 4. Añadir archivos al repositorio
echo "Agregando archivos al índice de Git..."
git add .

# 5. Configurar identidad local en el repositorio (evita error de detección)
echo "Configurando identidad local de Git para este repositorio..."
git config user.email "alvarozapata04@gmail.com"
git config user.name "Álvaro Zapata Beteta"

# 6. Crear el primer commit
echo "Creando commit inicial..."
git commit -m "Initial commit: Álvaro Zapata's QML TFG Portfolio & Glicina Digital Twin"

# 7. Configurar el origen remoto
echo "Configurando repositorio remoto en GitHub..."
# Eliminar origen si ya existe para evitar errores de duplicado
git remote remove origin 2>/dev/null
git remote add origin https://github.com/Alvarozb04/TFG.git

# 8. Renombrar rama a main
git branch -M main

# 9. Subir código a GitHub
echo "Subiendo código a GitHub (se te solicitarán tus credenciales de GitHub)..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ ¡Código subido con éxito a GitHub!"
    echo "Ahora puedes activar GitHub Pages desde la pestaña 'Settings' -> 'Pages' de tu repositorio para publicar tu visualizador 3D."
else
    echo "❌ Hubo un error al subir el código a GitHub."
    echo "Asegúrate de haber creado previamente el repositorio vacío 'TFG' en tu cuenta de GitHub (https://github.com/Alvarozb04/TFG)."
fi
