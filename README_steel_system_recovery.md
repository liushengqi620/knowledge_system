# 钢铁全流程实时异常预警溯源系统 - 主要代码恢复说明

当前 Codex 执行环境只能看到 C: 和 D:，看不到源项目所在的 E: 盘，所以无法由工具直接跨盘复制源文件。

请在你本机普通 PowerShell 中运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
D:\codex_recovery\copy_main_steel_system.ps1
```

脚本会从：

`E:\lsq\Project\数据知识抽取`

复制主要系统代码到：

`D:\codex_recovery`

复制范围：

- Scripts/steel_realtime_system.py
- Scripts/steel_realtime_fastapi.py
- Scripts/steel_realtime_deployment_package.py
- 相关测试与验收脚本
- apps/steel-realtime-vben
- knowledge_exports/steel_realtime_system_v1

运行后查看：

`D:\codex_recovery\copy_summary.txt`

启动系统命令：

```powershell
cd /d D:\codex_recovery
C:\Users\14182\miniconda3\envs\steel_knowledge_data_env\python.exe -m uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018
```
