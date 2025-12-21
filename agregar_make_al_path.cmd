@echo off
REM Ejecutar como administrador
SETLOCAL
set "MAKERUTA=C:\Program Files (x86)\GnuWin32\bin"

REM Verifica si la ruta ya está en el PATH
ECHO %PATH% | find /I "%MAKERUTA%" >nul
IF %ERRORLEVEL%==0 (
    echo La ruta ya está en el PATH del sistema.
    GOTO :EOF
)

REM Agrega la ruta al PATH del sistema
set "KEY=HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
for /f "tokens=2*" %%A in ('reg query "%KEY%" /v Path') do set "OLDPATH=%%B"
set "NEWPATH=%OLDPATH%;%MAKERUTA%"
reg add "%KEY%" /v Path /d "%NEWPATH%" /f

echo Listo. Reinicia la terminal para que los cambios tengan efecto.
ENDLOCAL
pause