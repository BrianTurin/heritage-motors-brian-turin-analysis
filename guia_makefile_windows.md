# Guía rápida: Uso de Makefile en Windows

Esta guía te ayudará a instalar y usar Makefile en Windows para automatizar tareas en este proyecto, incluso si nunca lo has hecho antes.

## ¿Qué es un Makefile?
Un Makefile es un archivo que contiene comandos para automatizar tareas comunes (por ejemplo, ejecutar scripts de Python) usando la herramienta `make`.

---

## 1. Instalar Make en Windows

### Opción recomendada: GnuWin32 Make

1. Abre PowerShell o tu navegador y descarga Make desde:
   http://gnuwin32.sourceforge.net/packages/make.htm
   (o usa el comando: `winget install GnuWin32.Make`)

2. Espera a que finalice la instalación.

---

## 2. Agregar Make al PATH

Para poder usar el comando `make` desde cualquier terminal, debes agregar la ruta de Make al PATH del sistema:

1. Busca la carpeta donde se instaló Make, normalmente:
   `C:\Program Files (x86)\GnuWin32\bin`

2. Ejecuta el script `agregar_make_al_path.cmd` incluido en este proyecto:
   - Haz clic derecho sobre el archivo y selecciona "Ejecutar como administrador".
   - Reinicia la terminal después de ejecutarlo.

---

## 3. Usar el Makefile

1. Abre una terminal (PowerShell o CMD) en la carpeta raíz del proyecto.
2. Escribe `make <tarea>` para ejecutar la tarea que desees. Ejemplo:
   ```
   make inventario-eoq-estacional-costo
   ```
3. Consulta el README principal para ver la lista de comandos disponibles y su descripción.

---

## 4. Solución de problemas

- Si el comando `make` no se reconoce, asegúrate de que la ruta esté en el PATH y reinicia la terminal.
- Si tienes dudas, revisa esta guía o pide ayuda a tu equipo.

---

¡Listo! Ahora puedes automatizar tareas fácilmente usando Makefile en Windows.