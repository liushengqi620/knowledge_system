# 钢铁全流程生产异常预警溯源系统实现说明

## 系统定位

当前系统面向钢铁生产过程中的品质异常风险监测、异常类别识别和连铸段缺陷路径溯源。界面采用 Vben Admin 风格的信息架构，当前版本为可离线打开、也可由本地服务驱动的实时演示原型。

系统不使用具体企业名称。全流程工艺图用于展示粗炼、精炼、中间包、结晶器、流量控制、传热冷却、品质检测之间的流程背景；单事件模型定位只限定在数据真实覆盖的连铸相关环节。

## 数据边界

当前数据能够支撑：

- 事件级品质异常风险概率展示。
- 六类粗粒度异常类别识别。
- 基于变量组、连铸工序区域、工艺状态、失稳机制和纠正建议的路径解释。
- 历史事件流模拟实时接入。

当前数据不应直接支撑：

- 单事件在粗炼或精炼阶段的真实定位。
- 跨全流程的强因果链判定。
- 仅凭 LLM 生成原因作为因果证据。

因此系统中的全流程图是工艺背景图，只有中间包、结晶器、流量控制、传热冷却和品质检测等连铸段节点属于模型分析范围。

## 三层功能

### 1. 异常预警

回答“当前事件是否存在品质异常风险”。输出包括事件 ID、风险概率、风险等级、边界状态和连铸段节点状态。

接口：

- `GET /risk/events`
- `GET /api/realtime/next?cursor=0`

### 2. 异常识别

回答“异常属于哪类质量异常，是否存在并发异常”。输出包括主异常组、多标签异常组、类别概率和置信度。

接口：

- `GET /identify/events/{event_id}`
- `GET /api/events/{event_id}`

### 3. 异常溯源

回答“异常为什么发生，沿着哪条连铸段证据链传播，应该如何处理”。路径层级为：

```text
窗口变量 -> 变量组 -> 连铸工序区域 -> 工艺状态 -> 失稳机制 -> 异常类别 -> 纠正建议
```

接口：

- `GET /api/trace/events/{event_id}`
- `GET /api/recommend/events/{event_id}`
- `GET /api/knowledge/search?q=keyword`

## 运行方式

生成系统页面和实时数据种子：

```powershell
python Scripts\steel_realtime_system.py --max-events 120 --output-dir knowledge_exports\steel_realtime_system_v1
```

启动本地实时服务：

```powershell
python Scripts\steel_realtime_system.py --max-events 120 --output-dir knowledge_exports\steel_realtime_system_v1 --serve --host 127.0.0.1 --port 8018
```

访问：

```text
http://127.0.0.1:8018
```

如果直接打开 `knowledge_exports/steel_realtime_system_v1/index.html`，系统会自动进入离线演示模式。

## 正式 Vben Admin 迁移建议

正式工程建议拆为：

- `apps/steel-realtime-web`: Vben Admin 前端工程。
- `services/steel-realtime-api`: FastAPI 或当前轻量 HTTP API 服务。
- `knowledge_exports/steel_realtime_system_v1`: 模型事件流、指标和解释结果。

页面模块建议：

- 实时生产总览：工艺动态图、实时事件流、风险 KPI。
- 异常预警：风险概率、风险等级、边界状态、lead horizon 指标。
- 异常识别：异常类别概率、多标签命中、类别分布。
- 异常溯源：交互式路径图、节点属性、链路详情、遮蔽下降、专家依据。
- 专家知识与建议：知识检索、纠正检查项、调整动作、复核动作。

正式接入实时数据时，应把当前历史事件流替换为消息队列、数据库轮询或 WebSocket 推送；前端展示逻辑和事件结构可以保持不变。
