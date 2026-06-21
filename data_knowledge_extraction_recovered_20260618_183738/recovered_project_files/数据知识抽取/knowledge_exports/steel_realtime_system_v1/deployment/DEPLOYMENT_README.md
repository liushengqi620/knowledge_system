# 钢铁全流程生产异常预警溯源系统部署包

该部署包用于运行和验收当前系统导出物：

```text
Z:/knowledge_exports/steel_realtime_system_v1
```

系统主线：

```text
实时数据接入 -> 异常预警 -> 异常识别 -> 连铸段路径溯源 -> 专家知识/LLM 辅助建议
```

## 数据边界

全流程图用于工艺背景和工业化展示。单事件定位、节点高亮和路径解释限定在连铸段模型分析范围；粗炼、精炼只作为流程上下文。

## 启动轻量服务

```powershell
.\start_lightweight_server.ps1
```

默认地址：

```text
http://127.0.0.1:8018
```

## 启动 FastAPI 服务

如果已安装 FastAPI/uvicorn：

```powershell
.\start_fastapi_server.ps1
```

## 实时能力

- SSE 推送：`GET /api/realtime/stream?cursor=0&limit=50`
- 轮询兜底：`GET /api/realtime/next?cursor=0`
- JSON 接入：`POST /api/realtime/ingest`
- 路径问答：`POST /api/assistant/path-question`

## 接入示例事件

```powershell
.\post_sample_event.ps1
```

## 验收

```powershell
.\run_acceptance.ps1
.\run_visual_acceptance.ps1
```

验收报告：

```text
Z:/knowledge_exports/steel_realtime_system_v1/system_acceptance_report.json
```

LLM 只用于辅助表达、检查项组织和纠正建议生成，不作为因果证据。
