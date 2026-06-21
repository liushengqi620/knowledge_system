# 运行手册

## 标准启动

1. 运行 `start_lightweight_server.ps1` 启动轻量后端。
2. 运行 `run_vben_preview.ps1` 启动前端预览。
3. 使用 `post_sample_event.ps1` 验证 JSON 实时接入。
4. 使用 `run_acceptance.ps1` 和 `run_visual_acceptance.ps1` 生成验收报告。

## 数据与证据边界

全流程图用于生产背景展示。单事件解释、节点高亮和路径溯源限定在连铸段模型分析范围。LLM/助手输出只用于说明和建议组织，不作为因果证据。

## 常用接口

- `GET /api/realtime/stream?cursor=0&limit=50`
- `GET /api/realtime/next?cursor=0`
- `POST /api/realtime/ingest`
- `POST /api/assistant/path-question`
