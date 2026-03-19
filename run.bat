@echo off
echo Iniciando entorno virtual...

if not exist venv\ (
    echo Creando entorno virtual...
    py -m venv venv
)

echo Activando entorno virtual e instalando dependencias...
call .\venv\Scripts\activate.bat
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

echo Iniciando el servidor FastAPI...
py -m uvicorn main:app --reload
pause
