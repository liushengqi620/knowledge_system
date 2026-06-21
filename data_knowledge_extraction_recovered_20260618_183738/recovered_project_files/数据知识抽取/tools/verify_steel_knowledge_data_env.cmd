@echo off
setlocal

cd /d E:\lsq\Project\数据知识抽取

set PYTHON_EXE=C:\Users\14182\miniconda3\envs\steel_knowledge_data_env\python.exe

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python not found: %PYTHON_EXE%
  exit /b 1
)

"%PYTHON_EXE%" -c "import sys; print('python=', sys.executable); import fastapi, uvicorn, pandas, sklearn; print('fastapi=', fastapi.__version__); print('uvicorn=', uvicorn.__version__); print('pandas=', pandas.__version__); print('sklearn=', sklearn.__version__)"
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" Scripts\verify_steel_realtime_system.py --output-dir knowledge_exports\steel_realtime_system_v1 --source-dir knowledge_exports\baosteel_three_level_system_v1
if errorlevel 1 exit /b 1

echo [OK] steel_knowledge_data_env verification passed.

endlocal
