@echo off
setlocal

cd /d E:\lsq\Project\数据知识抽取

set CONDA_NO_PLUGINS=true
set CONDA_OVERRIDE_CUDA=0
set PYTHON_EXE=C:\Users\14182\miniconda3\envs\steel_knowledge_data_env\python.exe

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python not found: %PYTHON_EXE%
  exit /b 1
)

echo [INFO] Using %PYTHON_EXE%
"%PYTHON_EXE%" -c "import sys; print(sys.executable); print(sys.version)"

echo [INFO] Upgrading pip tooling
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel -i https://pypi.org/simple
if errorlevel 1 exit /b 1

echo [INFO] Installing backend dependencies
"%PYTHON_EXE%" -m pip install fastapi uvicorn -i https://pypi.org/simple
if errorlevel 1 exit /b 1

echo [INFO] Installing data/model dependencies
"%PYTHON_EXE%" -m pip install pandas scikit-learn numpy scipy joblib -i https://pypi.org/simple
if errorlevel 1 exit /b 1

echo [INFO] Verifying environment
"%PYTHON_EXE%" -c "import fastapi, uvicorn, pandas, sklearn, numpy, scipy; print('steel_knowledge_data_env ok')"
if errorlevel 1 exit /b 1

echo [OK] steel_knowledge_data_env configured.
echo To start backend:
echo conda activate steel_knowledge_data_env
echo cd /d E:\lsq\Project\数据知识抽取
echo python -m uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018

endlocal
