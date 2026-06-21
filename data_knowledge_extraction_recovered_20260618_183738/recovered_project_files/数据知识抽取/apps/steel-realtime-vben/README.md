# 钢铁全流程生产异常预警溯源 Vben Admin 模块

该目录是面向 Vben Admin 的前端模块包，用于接入当前后端：

```text
Scripts/steel_realtime_fastapi.py
Scripts/steel_realtime_system.py
```

系统名称统一为“钢铁全流程生产异常预警溯源系统”，不绑定具体企业名称。

## 模块内容

- `src/views/steel-realtime/index.vue`：三层实时工作台主页面。
- `src/components/ProcessDigitalTwin.vue`：全流程数字孪生背景与连铸段状态节点。
- `src/components/EventStreamPanel.vue`：实时告警流。
- `src/components/TraceabilityPathGraph.vue`：可交互路径溯源图。
- `src/api/steelRealtime.ts`：后端 API client。
- `src/types/steelRealtime.ts`：事件、路径、建议和知识条目类型。
- `src/router/routes.ts`：Vben Admin 路由片段。

## 后端要求

启动正式 FastAPI 服务：

```powershell
uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018
```

或启动内置轻量服务：

```powershell
python Scripts\steel_realtime_system.py --max-events 120 --output-dir knowledge_exports\steel_realtime_system_v1 --serve --host 127.0.0.1 --port 8018
```

## 前端接入方式

将 `src` 下的 API、types、components、views 和 router 文件合并进现有 Vben Admin 工程，并在主路由中合并：

```ts
import { steelRealtimeRoutes } from './steel-realtime/routes';

export default [...steelRealtimeRoutes];
```

配置 API 地址：

```text
VITE_STEEL_REALTIME_API_BASE=http://127.0.0.1:8018
```

## 数据边界

全流程图用于工艺背景和工业化展示。单事件定位、路径解释和节点高亮只使用连铸段模型分析范围，包括中间包、结晶器、流量控制、传热冷却和品质检测等节点。

路径问答与专家知识检索用于辅助表达和纠正建议，不作为因果证据。
