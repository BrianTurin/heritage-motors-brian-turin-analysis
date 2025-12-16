# ==========================================
# Script de Ejecución Completa
# Proyecto Investigación Operativa
# ==========================================
# Ejecutar desde PowerShell: .\run_all.ps1
# ==========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PROYECTO INVESTIGACIÓN OPERATIVA" -ForegroundColor Cyan
Write-Host "  UTN FRCU - 2025" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en la raíz del proyecto
if (-not (Test-Path "src")) {
    Write-Host "ERROR: Ejecuta este script desde la raíz del proyecto (donde está la carpeta src/)" -ForegroundColor Red
    exit 1
}

# Activar entorno virtual
Write-Host "[1/5] Activando entorno virtual..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\activate.ps1") {
    .\.venv\Scripts\activate.ps1
} else {
    Write-Host "  ADVERTENCIA: No se encontró .venv. Usando Python del sistema." -ForegroundColor Yellow
}

# Preprocesamiento
Write-Host ""
Write-Host "[2/5] Ejecutando preprocesamiento..." -ForegroundColor Yellow
python src/preprocessing/01_limpiar_dataset.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error en 01_limpiar_dataset.py" -ForegroundColor Red; exit 1 }

python src/preprocessing/02_generar_ventas_mensuales.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error en 02_generar_ventas_mensuales.py" -ForegroundColor Red; exit 1 }

# Análisis (opcional pero recomendado)
Write-Host ""
Write-Host "[3/5] Ejecutando análisis ABC/XYZ..." -ForegroundColor Yellow
python src/analysis/ABC_analysis.py
python src/analysis/XYZ_analisis.py

# Pronóstico Prophet (requerido para inventario)
Write-Host ""
Write-Host "[4/5] Ejecutando modelo Prophet..." -ForegroundColor Yellow
python src/forecast/prophet_forecast.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error en prophet_forecast.py" -ForegroundColor Red; exit 1 }

# Políticas de inventario
Write-Host ""
Write-Host "[5/5] Ejecutando políticas de inventario..." -ForegroundColor Yellow
python src/inventory/eoq_estacional.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error en eoq_estacional.py" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ¡EJECUCIÓN COMPLETADA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Resultados guardados en:" -ForegroundColor Cyan
Write-Host "  - outputs/forecast/   (pronósticos)" -ForegroundColor White
Write-Host "  - outputs/inventory/  (políticas EOQ)" -ForegroundColor White
Write-Host ""
