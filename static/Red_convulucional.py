import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# =====================================================================
# 1. CONFIGURACIÓN DE LOS DATOS (Rutas a tus carpetas)
# =====================================================================
# Pon aquí las rutas exactas donde tienes tus carpetas 'train' y 'test'
RUTA_TRAIN = "ruta/a/tus/datos/train" 
RUTA_TEST  = "ruta/a/tus/datos/test"

# =====================================================================
# 2. PREPROCESAMIENTO
# =====================================================================
transformaciones = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor() # Convierte a matriz y divide por 255 (escala 0.0 a 1.0)
])

# =====================================================================
# 3. LA ARQUITECTURA DE LA RED (Convoluciones + Clasificador)
# =====================================================================
class DermoScanCNN(nn.Module):
    def __init__(self):
        super(DermoScanCNN, self).__init__()
        
        # Convoluciones (Extracción)
        self.bloques_conv = nn.Sequential(
            # Bloque 1
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Bloque 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Bloque 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        # Red Densa (Clasificación)
        self.clasificador = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(128, 64), 
            nn.ReLU(),          
            nn.Dropout(p=0.5),
            nn.Linear(64, 1),   
            nn.Sigmoid()        
        )

    def forward(self, x):
        x = self.bloques_conv(x)
        x = self.global_pool(x)
        x = torch.flatten(x, 1) 
        x = self.clasificador(x)
        return x

# =====================================================================
# 4. FUNCIONES PARA DIBUJAR LAS GRÁFICAS
# =====================================================================
def dibujar_curvas(historial_train, historial_val, titulo, ylabel):
    plt.figure(figsize=(8, 6))
    plt.plot(historial_train, label='Entrenamiento (Train)', color='blue', linewidth=2)
    plt.plot(historial_val, label='Validación (Test)', color='orange', linewidth=2, linestyle='--')
    plt.title(titulo)
    plt.xlabel('Épocas')
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.show()

def dibujar_roc(etiquetas_reales, predicciones):
    # Calcula la curva ROC y el Área Bajo la Curva (AUC)
    fpr, tpr, umbrales = roc_curve(etiquetas_reales, predicciones)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'Curva ROC (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--') # Línea de suerte (50%)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Tasa de Falsos Positivos (FPR)')
    plt.ylabel('Tasa de Verdaderos Positivos (TPR)')
    plt.title('Curva ROC (Receiver Operating Characteristic)')
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.show()

# =====================================================================
# 5. BUCLE DE ENTRENAMIENTO Y VALIDACIÓN
# =====================================================================
def entrenar_y_evaluar():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo de cálculo: {device}")

    # --- CARGA AUTOMÁTICA DE DATOS ---
    try:
        # ImageFolder asigna 0 a la primera carpeta (benignos) y 1 a la segunda (malignos)
        dataset_train = datasets.ImageFolder(root=RUTA_TRAIN, transform=transformaciones)
        dataset_test = datasets.ImageFolder(root=RUTA_TEST, transform=transformaciones)
    except FileNotFoundError:
        print("⚠️ CUIDADO: No se encontraron las carpetas reales. Creando datos falsos para que el código no falle.")
        # Simulación solo para que puedas probar el código si aún no tienes las fotos puestas
        X_dummy = torch.rand(100, 3, 224, 224) 
        Y_dummy = torch.randint(0, 2, (100,)).long()
        dataset_train = torch.utils.data.TensorDataset(X_dummy, Y_dummy)
        dataset_test = torch.utils.data.TensorDataset(X_dummy[:20], Y_dummy[:20])

    dataloader_train = DataLoader(dataset_train, batch_size=16, shuffle=True)
    dataloader_test = DataLoader(dataset_test, batch_size=16, shuffle=False)

    modelo = DermoScanCNN().to(device)
    criterio = nn.BCELoss() # Función de pérdida para binario
    optimizador = optim.Adam(modelo.parameters(), lr=0.001)

    epocas = 15
    
    # Listas para guardar la historia y luego dibujar las gráficas
    historia_loss_train = []
    historia_loss_val = []
    
    # Listas para la Curva ROC (solo guardamos las de la última época)
    todas_las_etiquetas_reales = []
    todas_las_predicciones = []

    for epoca in range(epocas):
        # --- FASE DE ENTRENAMIENTO ---
        modelo.train() 
        loss_train_acumulada = 0.0
        
        for imagenes, etiquetas in dataloader_train:
            imagenes = imagenes.to(device)
            # Adaptamos la etiqueta a [Batch, 1] y Float para la función BCELoss
            etiquetas = etiquetas.float().unsqueeze(1).to(device)
            
            predicciones = modelo(imagenes)
            loss = criterio(predicciones, etiquetas)
            
            optimizador.zero_grad()
            loss.backward()
            optimizador.step()
            
            loss_train_acumulada += loss.item()
            
        loss_train_media = loss_train_acumulada / len(dataloader_train)
        historia_loss_train.append(loss_train_media)

        # --- FASE DE VALIDACIÓN (TEST) ---
        modelo.eval() # Modo evaluación (desactiva el Dropout para testear justamente)
        loss_val_acumulada = 0.0
        
        # Limpiamos las listas ROC en cada época para quedarnos solo con el examen final
        todas_las_etiquetas_reales = []
        todas_las_predicciones = []

        with torch.no_grad(): # No calculamos gradientes (ahorra memoria y tiempo)
            for imagenes, etiquetas in dataloader_test:
                imagenes = imagenes.to(device)
                etiquetas = etiquetas.float().unsqueeze(1).to(device)
                
                predicciones = modelo(imagenes)
                loss_val = criterio(predicciones, etiquetas)
                loss_val_acumulada += loss_val.item()
                
                # Guardamos datos para la curva ROC
                todas_las_etiquetas_reales.extend(etiquetas.cpu().numpy())
                todas_las_predicciones.extend(predicciones.cpu().numpy())
                
        loss_val_media = loss_val_acumulada / len(dataloader_test)
        historia_loss_val.append(loss_val_media)

        print(f"Época [{epoca+1}/{epocas}] | Train Loss: {loss_train_media:.4f} | Val (Test) Loss: {loss_val_media:.4f}")

    print("\n¡Entrenamiento completado! Generando gráficas...")
    
    # 1. Dibujamos la Curva de Pérdida (Loss)
    dibujar_curvas(historia_loss_train, historia_loss_val, 
                   titulo="Curva de Función de Pérdida (Loss)", ylabel="Pérdida (BCELoss)")
    
    # 2. Dibujamos la Curva ROC
    dibujar_roc(todas_las_etiquetas_reales, todas_las_predicciones)

    return modelo

if __name__ == "__main__":
    modelo_entrenado = entrenar_y_evaluar()