<template>
  <main class="steel-shell">
    <section class="steel-main">
      <header class="topbar">
        <div class="top-title">
          <strong>钢铁全流程质量异常管控系统</strong>
          <h1>{{ activeModuleMeta.title }}</h1>
          <p>{{ activeModuleMeta.subtitle }}</p>
        </div>
        <div class="top-status">
          <span :class="['status-pill', running ? 'ok' : 'idle']">{{ running ? '实时数据流运行中' : '实时数据流待启动' }}</span>
          <span class="status-pill">{{ lineName(activeEvent?.line_id) }}</span>
          <span class="status-pill">依据库 {{ basisCount }} 条</span>
        </div>
      </header>

      <section class="module-tabs">
        <button
          v-for="module in modules"
          :key="module.key"
          :class="{ active: activeModule === module.key }"
          :style="{ '--module-bg': `url(${module.background})` }"
          type="button"
          @click="activeModule = module.key"
        >
          <img :src="module.icon" :alt="`${module.title}图标`" class="module-tab__thumb" />
          <span class="module-tab__copy">
            <b>{{ module.title }}</b>
            <small>{{ module.subtitle }}</small>
          </span>
        </button>
      </section>
      <span class="sr-only">生产总览</span>

      <section class="toolbar">
        <button type="button" class="primary" @click="toggleStream">
          {{ running ? '暂停流' : '启动流' }}
        </button>
        <button type="button" @click="loadNextEvent">下一条事件</button>
        <button type="button" @click="goModule('trace')">品质预警</button>
        <button type="button" @click="goModule('basis')">知识维护</button>
        <label class="upload">
          接入事件
          <input type="file" accept=".json" @change="handleUpload" />
        </label>
      </section>

      <section class="kpi-grid">
        <article class="kpi">
          <span>当前事件</span>
          <strong>{{ activeEventTitle }}</strong>
        </article>
        <article class="kpi">
          <span>风险等级</span>
          <strong>{{ riskLevelName(activeEvent?.risk_warning?.risk_level) }}</strong>
        </article>
        <article class="kpi">
          <span>风险值</span>
          <strong>{{ fmt(activeEvent?.risk_warning?.risk_probability) }}</strong>
        </article>
        <article class="kpi">
          <span>溯源可信度</span>
          <strong>{{ fmt(topPath?.final_score || topPath?.path_score) }}</strong>
        </article>
      </section>

      <section v-if="activeModule === 'overview'" class="workspace">
        <div class="top-grid">
          <ProcessDigitalTwin
            :active-event="activeEvent"
            :labels="seed?.display_labels || {}"
            :steps="activeEvent?.process_status || seed?.process_steps || []"
            @select-step="selectStep"
          />
          <EventStreamPanel
            :active-event-id="activeEvent?.event_id"
            :events="visibleEvents"
            :labels="seed?.display_labels || {}"
            :running="running"
            @select-event="selectEvent"
          />
        </div>
        <article class="panel inference-chain realtime-chain-card">
          <div class="section-head">
            <h2>告警处置链路</h2>
            <span class="muted">当前事件从生产信号进入预警、判别、原因复核和现场处置</span>
          </div>
          <div class="inference-steps">
            <div v-for="step in inferenceSteps" :key="step.key" class="inference-step">
              <span>{{ step.title }}</span>
              <strong>{{ step.value }}</strong>
              <small>{{ step.note }}</small>
              <i :style="{ width: `${Math.round(step.confidence * 100)}%` }" />
            </div>
          </div>
        </article>
        <article class="panel model-flow-card">
          <div class="section-head">
            <div>
              <h2>质量模型运行状态</h2>
              <span class="muted">按现场处置流程：异常预警、异常种类判断、关联异常提示、溯源证据复核</span>
            </div>
            <button type="button" @click="refreshModelArtifacts">刷新模型结果</button>
          </div>
          <div class="model-flow-grid">
            <div v-for="stage in cascadePipeline" :key="stage.stage" class="model-stage-card">
              <span>{{ stageDisplayName(stage) }}</span>
              <strong>{{ stageOutputName(stage) }}</strong>
              <small v-for="[key, value] in entries(stage.metric)" :key="key">{{ evidenceLabel(key) }}：{{ evidenceValue(value) }}</small>
            </div>
          </div>
          <div class="model-metric-row">
            <div v-for="item in cascadeMetrics" :key="item.key" class="model-metric">
              <span>{{ item.displayTitle || item.title }}</span>
              <strong>{{ item.level || fmt(item.value) }}</strong>
              <small>{{ item.processNote || item.note }}</small>
              <small class="metric-raw">{{ item.raw }}</small>
              <i :style="{ width: `${Math.round(item.value * 100)}%` }" />
            </div>
          </div>
        </article>
        <section class="visual-asset-grid">
          <article class="visual-asset-card">
            <img src="/steel_realtime_workshop_bg.png" alt="实时生产现场监控示意" />
            <div>
              <span>实时现场</span>
              <h2>产线状态与事件窗口</h2>
              <p>用于承接实时数据接入、状态刷新和告警触发，不再只作为页面背景。</p>
            </div>
          </article>
          <article class="visual-asset-card">
            <img src="/steel_evidence_fusion_graph.png" alt="质量证据融合示意" />
            <div>
              <span>证据融合</span>
              <h2>信号、规则与知识证据</h2>
              <p>把实时生产信号、历史经验和文本知识组织成可追踪的证据包。</p>
            </div>
          </article>
          <article class="visual-asset-card">
            <img src="/steel_abnormal_propagation_graph.png" alt="质量异常传播链路示意" />
            <div>
              <span>异常传播</span>
              <h2>从工序扰动到质量风险</h2>
              <p>展示候选根因如何沿工序、设备区域和缺陷机理逐步传递。</p>
            </div>
          </article>
        </section>
        <div class="analysis-grid">
          <article class="panel alarm-card">
            <div class="section-head">
              <h2>当前质量告警</h2>
              <button type="button" @click="goModule('trace')">进入台账</button>
            </div>
            <div class="risk-ring" :style="{ '--p': riskPercent }">
              <strong>{{ fmt(activeEvent?.risk_warning?.risk_probability) }}</strong>
            </div>
            <p>处置优先级：{{ riskActionText }}</p>
            <p>当前关注工序：{{ selectedStepLabel }}</p>
          </article>
          <article class="panel">
            <div class="section-head">
              <h2>异常识别结果</h2>
              <button type="button" @click="goModule('trace')">查看原因</button>
            </div>
            <div v-for="[key, value] in probabilityRows" :key="key" class="prob-row">
              <span>{{ displayLabel(key) }}</span>
              <b>{{ fmt(value) }}</b>
              <i :style="{ width: `${Math.round(Number(value) * 100)}%` }" />
            </div>
          </article>
          <article class="panel">
            <div class="section-head">
              <h2>当前处置要点</h2>
              <button type="button" @click="goModule('trace')">处置闭环</button>
            </div>
            <p>{{ activeEvent?.recommendation?.risk_summary || '暂无处置建议' }}</p>
            <ul>
              <li v-for="item in activeEvent?.recommendation?.recommended_checks || []" :key="item">
                {{ item }}
              </li>
            </ul>
          </article>
        </div>
      </section>

      <section v-else-if="activeModule === 'trace'" class="workspace">
        <article class="panel inference-chain trace-summary-card">
          <div class="section-head">
            <h2>当前事件处置摘要</h2>
            <span class="muted">{{ activeEventTitle }}</span>
          </div>
          <div class="inference-steps">
            <div v-for="step in inferenceSteps" :key="step.key" class="inference-step">
              <span>{{ step.title }}</span>
              <strong>{{ step.value }}</strong>
              <small>{{ step.note }}</small>
              <i :style="{ width: `${Math.round(step.confidence * 100)}%` }" />
            </div>
          </div>
        </article>
        <div class="two-col">
          <article class="panel trace-summary-card">
            <div class="section-head">
              <h2>当前告警台账</h2>
              <span class="muted">近期高风险事件优先处置</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>事件</th>
                  <th>风险</th>
                  <th>异常类别</th>
                  <th>建议动作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in warningRows.slice(0, 6)" :key="event.event_id" @click="selectEvent(event.event_id)">
                  <td>{{ eventTitle(event) }}</td>
                  <td>{{ riskLevelName(event.risk_warning.risk_level) }} / {{ fmt(event.risk_warning.risk_probability) }}</td>
                  <td>{{ displayGroups(event).join('、') || '-' }}</td>
                  <td>{{ event.recommendation.recommended_checks?.[0] || '待复核' }}</td>
                </tr>
              </tbody>
            </table>
          </article>
          <article class="panel trace-summary-card">
            <h2>处置闭环</h2>
            <p>{{ activeEvent?.recommendation?.risk_summary || '暂无建议' }}</p>
            <h3>现场检查</h3>
            <ul>
              <li v-for="item in activeEvent?.recommendation?.recommended_checks || []" :key="item">{{ item }}</li>
            </ul>
            <h3>复核记录</h3>
            <textarea v-model="feedback" placeholder="记录现场复核结论、处置动作、责任班组和复判结果" />
            <button type="button" class="primary feedback-btn" @click="saveFeedback">沉淀为知识候选</button>
            <div class="case-ingest-status">{{ knowledgeIngestStatus }}</div>
          </article>
        </div>
        <article class="panel model-gate-card">
          <div class="section-head">
            <div>
              <h2>预警判定与候选证据</h2>
              <span class="muted">判断为无品质异常时不触发处置；判断为异常时进入异常种类判断、关联异常提示和溯源证据排序</span>
            </div>
            <span class="status-pill ok">{{ cascadeModel?.status || '待加载' }}</span>
          </div>
          <div class="gate-grid">
            <div class="gate-policy">
              <b>预警判定规则</b>
              <p>{{ gatePolicyNormalRule }}</p>
              <p>{{ gatePolicyAbnormalRule }}</p>
              <div class="model-dataset-row">
                <span>主任务样本 {{ evidenceValue(modelDatasetStats.n_rows) }}</span>
                <span>辅助样本 {{ evidenceValue(modelDatasetStats.n_auxiliary_rows) }}</span>
                <span>多异常共存 {{ evidenceValue(modelDatasetStats.multiple_target_sample_count) }}</span>
              </div>
            </div>
            <div class="model-feature-list">
              <b>异常相关参数</b>
              <span v-for="parameter in abnormalParameterRows" :key="parameter.key">
                {{ parameter.label }} / {{ parameter.group }}
                <i>排查优先级 {{ parameter.priority }}</i>
              </span>
            </div>
          </div>
          <div class="cascade-evidence-list">
            <button
              v-for="row in cascadeEvidenceRows"
              :key="String(row.record_id)"
              type="button"
              @click="basisQuery = String(row.cascade_final_label || ''); searchBasis()"
            >
              <b>{{ evidenceLabel(String(row.cascade_final_label || '候选事件')) }}</b>
              <span>{{ row.process_time }}｜主类得分 {{ fmt(Number(row.cascade_main_class_score || 0)) }}</span>
              <small>{{ evidenceText(String(row.top_companion_abnormal_scores || row.top_class_evidence_features || '')) }}</small>
            </button>
          </div>
        </article>
        <article class="panel visual-frame-card">
          <img
            src="/steel_abnormal_propagation_graph.png"
            alt="异常传播链路图谱框架"
            class="visual-frame-card__image"
          />
          <div class="visual-frame-card__copy">
            <span>溯源框架图</span>
            <h2>从实时信号到缺陷风险的传播链路</h2>
            <p>
              当前事件先由生产信号触发预警，再沿工序区域、失稳机理和缺陷证据形成候选原因链路。
            </p>
            <div class="visual-frame-card__metrics">
              <b>{{ selectedStepLabel }}</b>
              <b>{{ displayLabel(topPath?.defect_mechanism || '') || '待定位机理' }}</b>
              <b>{{ fmt(topPath?.final_score || topPath?.path_score) }}</b>
            </div>
          </div>
        </article>
        <TraceabilityPathGraph
          :labels="seed?.display_labels || {}"
          :paths="activeEvent?.traceability?.top_k_paths || []"
        />
        <div class="evidence-grid">
          <article class="panel">
            <h2>生产信号依据</h2>
            <div class="metric-list">
              <span v-for="[key, value] in entries(activeEvidence?.structured_signal)" :key="key">
                {{ evidenceLabel(key) }}：{{ evidenceValue(value) }}
              </span>
            </div>
          </article>
          <article class="panel">
            <h2>工艺经验依据</h2>
            <div class="metric-list">
              <span v-for="[key, value] in entries(activeEvidence?.graph_evidence)" :key="key">
                {{ evidenceLabel(key) }}：{{ evidenceValue(value) }}
              </span>
            </div>
          </article>
          <article class="panel">
            <div class="section-head">
              <h2>资料片段</h2>
              <button type="button" @click="goModule('basis')">查看依据库</button>
            </div>
            <p v-for="item in activeEvidence?.text_evidence || []" :key="String(item.source_id)">
              {{ evidenceText(item.snippet) }}
            </p>
          </article>
        </div>
      </section>

      <section v-else-if="activeModule === 'basis'" class="workspace">
        <article class="panel knowledge-hub-card">
          <div class="section-head">
            <div>
              <h2>质量知识治理中心</h2>
              <span class="muted">把生产依据、候选知识、术语版本和历史复盘收敛到同一条审核闭环</span>
            </div>
            <span class="status-pill ok">正式图谱仅引用已审核知识</span>
          </div>
          <div class="knowledge-hub-grid">
            <span>
              <b>生产依据检索</b>
              <small>查工艺依据、历史链路、文本证据和专家规则</small>
            </span>
            <span>
              <b>候选知识审核</b>
              <small>判断新知识是合并、新建、重叠还是冲突</small>
            </span>
            <span>
              <b>术语与版本维护</b>
              <small>维护实体别名、关系融合、图谱版本和发布状态</small>
            </span>
            <span>
              <b>复盘入图闭环</b>
              <small>把处置反馈沉淀为候选实体、关系和证据来源</small>
            </span>
          </div>
        </article>
        <div class="summary-grid">
          <article class="panel kg-overview-card">
            <h2>工艺依据覆盖</h2>
            <div class="metric-list">
              <span>工艺/机理/变量条目：{{ basisCount }}</span>
              <span>异常原因链路：{{ seed?.knowledge_graph?.summary.path_template_count || 0 }}</span>
              <span>覆盖异常类型：{{ seed?.knowledge_graph?.summary.mechanism_coverage?.length || 0 }}</span>
            </div>
          </article>
          <article class="panel span-2 kg-search-card">
            <h2>依据检索</h2>
            <div class="query-row">
              <input v-model="basisQuery" placeholder="输入工序、变量或异常名称" />
              <button type="button" @click="searchBasis">检索依据</button>
            </div>
            <div class="basis-results">
              <article v-for="item in basisResults" :key="basisResultKey(item)" class="basis-result-card">
                <div class="basis-result-head">
                  <span>{{ knowledgeTypeLabel(item.type) }}</span>
                  <b>{{ item.title }}</b>
                </div>
                <p>{{ evidenceText(item.summary || item.content || '生产依据条目') }}</p>
                <div class="basis-result-meta">
                  <small v-if="item.scope">范围：{{ fieldLabel(item.scope) }}</small>
                  <small v-if="item.source_type">来源：{{ sourceTypeLabel(item.source_type) }}</small>
                  <small v-if="item.relation_type">关系：{{ relationTypeLabel(item.relation_type) }}</small>
                  <small v-if="item.event_count">历史命中：{{ item.event_count }} 次</small>
                  <small v-if="item.evidence_count">证据累计：{{ item.evidence_count }} 次</small>
                  <small v-if="typeof item.confidence === 'number'">置信度：{{ fmt(item.confidence) }}</small>
                </div>
                <i v-if="item.content">{{ evidenceText(item.content) }}</i>
              </article>
              <div v-if="!basisResults.length" class="basis-empty">暂无匹配依据，可尝试输入“结晶器”“传热”“中间包”“流量”等工艺术语。</div>
            </div>
          </article>
        </div>
        <article class="panel candidate-review-card">
          <div class="section-head">
            <div>
              <h2>候选知识审核</h2>
              <span class="muted">复盘或文本抽取得到的新知识，先做重复、重叠、冲突和新建判断，再由人工确认</span>
            </div>
            <span class="status-pill">{{ candidateStatusLabel(candidateValidation?.status) }}</span>
          </div>
          <div class="candidate-review-grid">
            <span v-for="item in candidateReviewSummary" :key="item.title">
              <b>{{ item.value }}</b>
              <small>{{ item.title }}</small>
              <i>{{ item.note }}</i>
            </span>
          </div>
          <div v-if="candidateValidation" class="candidate-validation-list">
            <b>{{ candidateValidation.recommendation }}</b>
            <span v-for="item in candidateValidationRows.slice(0, 8)" :key="String(item.candidate_id)">
              {{ item.candidate_label }}：{{ item.action }}
              <small v-if="typeof item.top_score === 'number'">匹配度 {{ fmt(item.top_score) }}</small>
            </span>
          </div>
          <p v-else class="muted">在“复盘知识入图”中生成候选后，这里会展示系统验证结果，辅助判断是否合并、挂别名、新建或冲突复核。</p>
        </article>
        <div class="kg-visual-grid">
          <article class="kg-visual-card kg-visual-process">
            <img src="/steel_process_knowledge_graph.png" alt="工艺机理知识图谱示意" class="kg-visual-card__image" />
            <div class="kg-visual-card__body">
              <span>图谱总览</span>
              <h2>工艺机理知识图谱</h2>
              <p>变量、工序、机理和缺陷类别的结构化关联。</p>
              <strong>{{ basisCount }} 个知识条目</strong>
            </div>
          </article>
          <article class="kg-visual-card kg-visual-fusion">
            <img src="/steel_evidence_fusion_graph.png" alt="多源证据融合图谱示意" class="kg-visual-card__image" />
            <div class="kg-visual-card__body">
              <span>证据融合</span>
              <h2>多源证据汇聚</h2>
              <p>生产信号、文本依据、专家规则和图谱事实汇入证据包。</p>
              <strong>{{ topPath?.evidence_sources?.length || 0 }} 条当前证据</strong>
            </div>
          </article>
          <article class="kg-visual-card kg-visual-propagation">
            <img src="/steel_abnormal_propagation_graph.png" alt="异常传播路径图谱示意" class="kg-visual-card__image" />
            <div class="kg-visual-card__body">
              <span>传播链路</span>
              <h2>异常传播路径</h2>
              <p>从工艺扰动到失稳机理，再到缺陷风险的链路表达。</p>
              <strong>{{ activeEvent?.traceability?.top_k_paths?.length || 0 }} 条候选路径</strong>
            </div>
          </article>
        </div>
        <article class="panel kg-network-card">
          <div class="section-head">
            <div>
              <h2>交互式知识图谱</h2>
              <span class="muted">按工序、变量、机理和处置关系展示正式图谱；点击节点查看证据，拖动节点可调整布局</span>
            </div>
            <span class="status-pill ok">{{ kgVisibleGraph.nodes.length }} 个节点 / {{ kgVisibleGraph.edges.length }} 条关系</span>
          </div>
          <div class="kg-graph-toolbar">
            <button
              v-for="scope in kgGraphScopes"
              :key="scope.key"
              :class="{ active: kgGraphScope === scope.key }"
              type="button"
              @click="setKgGraphScope(scope.key)"
            >
              {{ scope.label }}
            </button>
            <input v-model="kgGraphQuery" placeholder="搜索实体、变量、机理或关系" />
            <select v-model="kgNodeTypeFilter" aria-label="节点类型筛选">
              <option v-for="type in kgNodeTypeOptions" :key="type" :value="type">
                {{ type === 'all' ? '全部节点' : entityTypeLabel(type) }}
              </option>
            </select>
            <select v-model="kgRelationTypeFilter" aria-label="关系类型筛选">
              <option v-for="type in kgRelationTypeOptions" :key="type" :value="type">
                {{ type === 'all' ? '全部关系' : relationTypeLabel(type) }}
              </option>
            </select>
            <button type="button" @click="resetKgGraphView">重置视图</button>
          </div>
          <div class="kg-fusion-strip">
            <span>
              <b>{{ kgFusionSummary?.mapped_entity_count || 0 }}</b>
              <small>当前事件映射实体</small>
            </span>
            <span>
              <b>{{ kgFusionSummary?.event_subgraph_node_count || kgVisibleGraph.nodes.length }}</b>
              <small>事件子图节点</small>
            </span>
            <span>
              <b>{{ kgFusionSummary?.event_subgraph_edge_count || kgVisibleGraph.edges.length }}</b>
              <small>事件子图关系</small>
            </span>
            <span :class="{ warning: (kgFusionSummary?.missing_link_count || 0) > 0 }">
              <b>{{ kgFusionSummary?.missing_link_count || 0 }}</b>
              <small>待补充关系</small>
            </span>
            <span>
              <b>{{ scoreLevel(kgFusionSummary?.avg_graph_prior || 0) }}</b>
              <small>图谱证据强度</small>
            </span>
          </div>
          <div class="kg-network-layout">
            <div class="kg-network-canvas">
              <div class="kg-canvas-tools">
                <button type="button" @click="zoomKgGraph(1.18)">+</button>
                <button type="button" @click="zoomKgGraph(0.84)">-</button>
                <button type="button" @click="fitKgGraph">适配</button>
                <button :class="{ active: kgShowLabels }" type="button" @click="kgShowLabels = !kgShowLabels">标签</button>
              </div>
              <div class="kg-legend">
                <span><i class="legend-process"></i>工序</span>
                <span><i class="legend-variable"></i>变量</span>
                <span><i class="legend-mechanism"></i>机理</span>
                <span><i class="legend-action"></i>处置</span>
              </div>
              <svg
                class="kg-graph-svg"
                viewBox="0 0 960 460"
                role="img"
                aria-label="可交互知识图谱"
                @wheel.prevent="onKgGraphWheel"
                @pointerdown="onKgGraphPanStart"
                @pointermove="onKgGraphPointerMove"
                @pointerup="stopKgNodeDrag"
                @pointerleave="stopKgNodeDrag"
              >
                <defs>
                  <marker id="kg-arrow" markerHeight="8" markerWidth="8" orient="auto" refX="7" refY="4">
                    <path d="M0,0 L8,4 L0,8 Z" fill="#4fdcff" />
                  </marker>
                  <filter id="kg-node-glow" x="-40%" y="-40%" width="180%" height="180%">
                    <feGaussianBlur stdDeviation="3.5" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>
                <g class="kg-grid-lines">
                  <line v-for="x in kgGridX" :key="`x-${x}`" :x1="x" :x2="x" y1="24" y2="436" />
                  <line v-for="y in kgGridY" :key="`y-${y}`" x1="24" x2="936" :y1="y" :y2="y" />
                </g>
                <g class="kg-viewport" :transform="kgGraphTransform">
                  <g class="kg-graph-edges">
                    <path
                      v-for="edge in kgVisibleGraph.edges"
                      :key="edge.id"
                      :class="{ active: edge.active }"
                      :d="kgEdgePath(edge)"
                      marker-end="url(#kg-arrow)"
                    />
                  </g>
                  <g class="kg-graph-nodes">
                    <g
                      v-for="node in kgVisibleGraph.nodes"
                      :key="node.id"
                      :class="['kg-node', `type-${node.type}`, { selected: node.selected, related: node.related, hovered: node.hovered, dimmed: kgSelectedNode && !node.selected && !node.related }]"
                      :transform="`translate(${node.x}, ${node.y})`"
                      role="button"
                      tabindex="0"
                      @click.stop="selectKgNode(node.id)"
                      @keydown.enter.prevent="selectKgNode(node.id)"
                      @pointerenter="hoveredKgNodeId = node.id"
                      @pointerleave="hoveredKgNodeId = ''"
                    @pointerdown.stop="onKgNodePointerDown(node.id, $event)"
                  >
                    <title>{{ node.fullLabel }} · {{ node.typeLabel }}</title>
                      <circle class="kg-node-halo" :r="node.radius + 7" />
                      <circle :r="node.radius" />
                      <rect
                        v-if="node.showLabel"
                        class="kg-node-label-bg"
                        :x="-(node.labelWidth / 2)"
                        :y="-(node.radius + 27)"
                        :width="node.labelWidth"
                        height="21"
                        rx="10.5"
                      />
                      <text v-if="node.showLabel" :y="-(node.radius + 10)">{{ node.label }}</text>
                      <text v-if="node.selected || node.hovered" :y="node.radius + 16" class="kg-node-type">{{ node.typeLabel }}</text>
                    </g>
                  </g>
                </g>
              </svg>
            </div>
            <aside class="kg-network-detail">
              <span class="status-pill">{{ kgSelectedNode ? entityTypeLabel(kgSelectedNode.type) : '等待选择' }}</span>
              <h3>{{ kgSelectedNode?.fullLabel || '选择图谱节点' }}</h3>
              <p>{{ kgSelectedNode ? kgNodeDescription(kgSelectedNode) : '点击左侧节点后，这里会显示实体类型、置信度、审核状态、别名和关联关系。' }}</p>
              <div v-if="kgSelectedNode" class="kg-node-meta">
                <span>置信度：{{ fmt(kgSelectedNode.confidence) }}</span>
                <span>审核状态：{{ reviewStatusLabel(kgSelectedNode.reviewStatus) }}</span>
                <span>证据累计：{{ kgSelectedNode.evidenceCount || 1 }} 次</span>
              </div>
              <div v-if="kgSelectedRelations.length" class="kg-selected-relations">
                <b>关联关系</b>
                <span v-for="edge in kgSelectedRelations.slice(0, 8)" :key="edge.id">
                  {{ edge.sourceLabel }} → {{ edge.targetLabel }}
                  <small>{{ relationTypeLabel(edge.type) }} / {{ fmt(edge.confidence) }}</small>
                </span>
              </div>
              <div v-if="kgSelectedNode" class="kg-governance-actions">
                <button type="button" @click="submitKgAction('mark_review_required')">标记待复核</button>
                <button type="button" @click="submitKgAction('request_merge')">申请合并</button>
                <button type="button" class="primary" @click="submitKgAction('publish_candidate')">发布候选</button>
              </div>
              <div class="case-ingest-status">{{ kgGovernanceStatus }}</div>
              <div v-if="kgMissingLinks.length" class="kg-selected-relations">
                <b>当前事件待补充关系</b>
                <span v-for="link in kgMissingLinks.slice(0, 5)" :key="`${link.source}-${link.relation_type}-${link.target}`">
                  {{ relationEndpointLabel(link.source) }} → {{ relationEndpointLabel(link.target) }}
                  <small>{{ relationTypeLabel(link.relation_type) }} / {{ link.label }}</small>
                </span>
              </div>
            </aside>
          </div>
        </article>
        <section class="kg-management-grid">
          <article class="panel kg-management-card">
            <div class="section-head">
              <h2>RAG 图谱版本与存储</h2>
              <span class="muted">轻量 JSON 展示，重型边特征由后端归档</span>
            </div>
            <div class="kg-asset-list">
              <span v-for="asset in kgVersionAssets" :key="asset.name">
                <b>{{ asset.name }}</b>
                <small>{{ asset.type }} / {{ asset.status }}</small>
                <i>{{ asset.detail }}</i>
              </span>
            </div>
          </article>
          <article class="panel kg-management-card">
            <div class="section-head">
              <h2>图谱实体预览</h2>
              <span class="muted">{{ seed?.knowledge_graph?.summary.node_count || 0 }} 个实体</span>
            </div>
            <div class="kg-chip-cloud">
              <span v-for="node in kgPreviewNodes" :key="node.id">
                <b>{{ fieldLabel(node.label) }}</b>
                <small>{{ entityTypeLabel(node.entity_type) }} / {{ reviewStatusLabel(node.review_status) }}</small>
              </span>
            </div>
          </article>
          <article class="panel kg-management-card">
            <div class="section-head">
              <h2>图谱关系预览</h2>
              <span class="muted">{{ seed?.knowledge_graph?.summary.edge_count || 0 }} 条关系</span>
            </div>
            <div class="kg-relation-list">
              <span v-for="edge in kgPreviewEdges" :key="edge.id">
                <b>{{ relationEndpointLabel(edge.source) }} 指向 {{ relationEndpointLabel(edge.target) }}</b>
                <small>{{ relationTypeLabel(edge.relation_type) }} / {{ sourceTypeLabel(edge.source_type) }} / {{ fmt(edge.confidence) }}</small>
              </span>
            </div>
          </article>
          <article class="panel kg-management-card kg-disambiguation-card">
            <div class="section-head">
              <h2>实体消歧融合</h2>
              <span class="muted">{{ kgDisambiguation?.policy || 'canonical_alias_type_scope_merge_v1' }}</span>
            </div>
            <div class="kg-asset-list">
              <span>
                <b>{{ kgDisambiguationStats.node_merge_count || 0 }}</b>
                <small>合并实体</small>
                <i>同义词、单位字段、英文缩写与中文工艺名归并</i>
              </span>
              <span>
                <b>{{ kgDisambiguationStats.edge_merge_count || 0 }}</b>
                <small>合并关系</small>
                <i>重复链路保留证据次数和最高置信度</i>
              </span>
              <span>
                <b>{{ kgDisambiguationStats.rule_count || 0 }}</b>
                <small>规则数</small>
                <i>规范名、同义词、类型隔离、证据累积、工艺一致性</i>
              </span>
            </div>
            <div class="kg-relation-list">
              <span v-for="node in kgMergedNodes" :key="node.id">
                <b>{{ fieldLabel(node.label) }}</b>
                <small>
                  {{ entityTypeLabel(node.entity_type) }} / {{ node.evidence_count || 1 }} 次证据 /
                  别名：{{ (node.aliases || []).map(fieldLabel).slice(0, 4).join('、') }}
                </small>
              </span>
            </div>
          </article>
        </section>
        <article class="panel kg-governance-card">
          <div class="section-head">
            <h2>知识图谱维护流程</h2>
            <span class="muted">RAG 产物不能直接覆盖生产图谱，需要审核、版本化和模型引用隔离</span>
          </div>
          <div class="kg-governance-flow">
            <span v-for="step in kgGovernanceFlow" :key="step.title">
              <b>{{ step.title }}</b>
              <small>{{ step.note }}</small>
            </span>
          </div>
        </article>
        <article class="panel kg-library-card">
          <h2>常用原因链路</h2>
          <div class="path-library">
            <span v-for="path in seed?.knowledge_graph?.path_library || []" :key="path.path_id">
              <b>{{ fieldLabel(path.variable_group) }} 关联 {{ fieldLabel(path.mechanism_label) }}</b>
              {{ fieldLabel(path.equipment_zone) }} · {{ path.event_count }} 次历史命中
            </span>
          </div>
        </article>
        <div class="two-col">
          <article class="panel kg-history-card">
            <h2>历史异常案例</h2>
            <div class="path-library">
              <span v-for="event in warningRows.slice(0, 6)" :key="event.event_id">
                <b>{{ eventTitle(event) }}</b>
                {{ lineName(event.line_id) }} · {{ riskLevelName(event.risk_warning.risk_level) }} · {{ event.recommendation.risk_summary }}
              </span>
            </div>
          </article>
          <article class="panel kg-ingest-card">
            <h2>复盘知识入图</h2>
            <p>确认有效的历史异常可生成候选实体、关系和证据，经审核后融合到知识图谱，用于后续实时溯源。</p>
            <div class="metric-list">
              <span>候选来源：历史异常案例、处置反馈、证据包</span>
              <span>入图内容：变量、工序、根因、处置动作、证据来源</span>
              <span>审核策略：人工确认后更新知识图谱版本</span>
            </div>
            <textarea v-model="feedback" placeholder="补充复盘结论，例如：现场确认二冷水量波动，已调整阀组并复判合格" />
            <button type="button" class="primary feedback-btn" @click="saveFeedback">生成入图候选</button>
            <div class="case-ingest-status">{{ knowledgeIngestStatus }}</div>
            <div v-if="caseIngestResult" class="candidate-list">
              <b>{{ caseIngestResult.batch_id }}</b>
              <span>目标图谱：{{ caseIngestResult.target_graph }}</span>
              <span>候选实体：{{ caseIngestResult.candidate_entities.length }} 个</span>
              <span>候选关系：{{ caseIngestResult.candidate_relations.length }} 条</span>
              <span v-for="relation in caseIngestResult.candidate_relations.slice(0, 3)" :key="relation.id">
                {{ relationTypeLabel(relation.relation_type) }}：{{ relationEndpointLabel(relation.source) }} 指向 {{ relationEndpointLabel(relation.target) }}
              </span>
            </div>
          </article>
        </div>
      </section>

      <section class="operation-log">
        <span v-for="item in operationLog.slice(-5)" :key="item">{{ item }}</span>
      </section>
      <button type="button" class="assistant-toggle" @click="assistantOpen = !assistantOpen">
        值班助手
      </button>
      <aside v-if="assistantOpen" class="assistant-drawer">
        <div class="section-head">
          <h2>值班助手</h2>
          <button type="button" @click="assistantOpen = false">关闭</button>
        </div>
        <p class="muted">助手只做解释、检索和记录辅助，不作为因果判断来源。</p>
        <div class="qa-row">
          <input v-model="question" placeholder="例如：当前事件应该优先检查哪个工序？" />
          <button type="button" class="primary" @click="askPathQuestion">询问</button>
        </div>
        <div class="answer">{{ answer }}</div>
        <div class="assistant-status">{{ assistantStatus }}</div>
        <div class="assistant-evidence">
          <b>当前事件依据</b>
          <span v-for="source in topPath?.evidence_sources || []" :key="source.source_id">
            {{ source.title }}：{{ evidenceText(source.snippet) }}
          </span>
        </div>
      </aside>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import {
  askAssistantPathQuestion,
  connectRealtimeStream,
  createCaseKnowledgeIngest,
  getCascadeModelSummary,
  getEventDetail,
  getKgEvidence,
  getKgEventSubgraph,
  getKgVersions,
  getTraceabilityEvidenceRows,
  getNextRealtimeEvent,
  getSteelRealtimeSeed,
  ingestRealtimeEvent,
  searchKnowledge,
  submitKgGovernanceAction,
  validateKnowledgeCandidate,
} from '../../api/steelRealtime';
import EventStreamPanel from '../../components/EventStreamPanel.vue';
import ProcessDigitalTwin from '../../components/ProcessDigitalTwin.vue';
import TraceabilityPathGraph from '../../components/TraceabilityPathGraph.vue';
import type {
  CaseKnowledgeIngestResponse,
  CascadeModelSummary,
  EvidencePackage,
  KgEventSubgraph,
  KgVersionResponse,
  KnowledgeEntity,
  KnowledgeItem,
  KnowledgeCandidateValidationResponse,
  KnowledgeRelation,
  SteelRealtimeEvent,
  SteelRealtimeSeed,
} from '../../types/steelRealtime';
import {
  STEEL_TERM_LABELS,
  eventDisplayTitle as formatEventDisplayTitle,
  eventTitle as formatEventTitle,
  formatEntityType,
  formatRelationType,
  formatReviewStatus,
  formatSourceType,
  formatSteelTerm,
  lineName as formatLineName,
  riskLevelName as formatRiskLevelName,
  sequenceName as formatSequenceName,
} from '../../utils/steelTerminology';

const modules = [
  {
    key: 'overview',
    title: '数据监控',
    subtitle: '实时数据、事件窗口与产线状态',
    icon: '/steel_icon_data_monitor.png',
    background: '/steel_realtime_process_bg.png',
  },
  {
    key: 'trace',
    title: '品质预警与溯源',
    subtitle: '异常种类判断、根因路径与处置建议',
    icon: '/steel_icon_quality_trace.png',
    background: '/steel_abnormal_propagation_graph.png',
  },
  {
    key: 'basis',
    title: '知识管理与维护',
    subtitle: '知识图谱、历史案例与复盘入图',
    icon: '/steel_icon_knowledge_maintenance.png',
    background: '/steel_process_knowledge_graph.png',
  },
] as const;

type ModuleKey = (typeof modules)[number]['key'];
type KgGraphScope = 'current' | 'process' | 'evidence' | 'all';
type KgPoint = { x: number; y: number };
type KgGraphView = { x: number; y: number; k: number };
type KgGraphNode = {
  id: string;
  label: string;
  fullLabel: string;
  type: string;
  typeLabel: string;
  confidence: number;
  reviewStatus?: string;
  evidenceCount?: number;
  sourceType?: string;
  aliases: string[];
  degree: number;
  x: number;
  y: number;
  radius: number;
  labelWidth: number;
  selected: boolean;
  related: boolean;
  hovered: boolean;
  showLabel: boolean;
};
type KgGraphEdge = {
  id: string;
  source: string;
  target: string;
  sourceLabel: string;
  targetLabel: string;
  type: string;
  confidence: number;
  active: boolean;
  sourceNode: KgGraphNode;
  targetNode: KgGraphNode;
};

const supportModules: Record<ModuleKey, { title: string; subtitle: string }> = {
  overview: modules[0],
  trace: modules[1],
  basis: modules[2],
};

const seed = ref<SteelRealtimeSeed>();
const events = ref<SteelRealtimeEvent[]>([]);
const activeEvent = ref<SteelRealtimeEvent>();
const activeEvidence = ref<EvidencePackage>();
const kgEventSubgraph = ref<KgEventSubgraph>();
const kgVersions = ref<KgVersionResponse>();
const cursor = ref(0);
const running = ref(false);
const activeModule = ref<ModuleKey>('overview');
const selectedStep = ref('');
const assistantOpen = ref(false);
const question = ref('');
const answer = ref('助手只用于值班解释和处置建议组织，不作为因果证据。');
const assistantStatus = ref('本地解释待命');
const basisQuery = ref('结晶器');
const basisResults = ref<KnowledgeItem[]>([]);
const kgGraphScope = ref<KgGraphScope>('current');
const kgGraphQuery = ref('');
const kgNodeTypeFilter = ref('all');
const kgRelationTypeFilter = ref('all');
const selectedKgNodeId = ref('');
const hoveredKgNodeId = ref('');
const kgDraggedNodeId = ref('');
const kgGraphView = ref<KgGraphView>({ x: 0, y: 0, k: 1 });
const kgPanStart = ref<{ x: number; y: number; view: KgGraphView }>();
const kgShowLabels = ref(false);
const kgNodePositions = ref<Record<string, KgPoint>>({});
const feedback = ref('');
const knowledgeIngestStatus = ref('待复盘确认');
const kgGovernanceStatus = ref('等待图谱维护操作');
const caseIngestResult = ref<CaseKnowledgeIngestResponse>();
const candidateValidation = ref<KnowledgeCandidateValidationResponse>();
const operationLog = ref<string[]>([]);
const cascadeModel = ref<CascadeModelSummary>();
const cascadeEvidenceRows = ref<Array<Record<string, unknown>>>([]);
let timer: number | undefined;
let eventSource: EventSource | undefined;

const kgGraphScopes: Array<{ key: KgGraphScope; label: string }> = [
  { key: 'current', label: '当前事件相关' },
  { key: 'process', label: '工艺机理网络' },
  { key: 'evidence', label: '高证据节点' },
  { key: 'all', label: '完整图谱' },
];
const kgGridX = [80, 200, 320, 440, 560, 680, 800, 920];
const kgGridY = [70, 140, 210, 280, 350, 420];

const activeModuleMeta = computed(() => supportModules[activeModule.value] || modules[0]);
const visibleEvents = computed(() => events.value.slice(Math.max(0, cursor.value - 14), cursor.value + 1));
const riskPercent = computed(() => Math.round(Number(activeEvent.value?.risk_warning?.risk_probability || 0) * 100));
const topPath = computed(() => activeEvent.value?.traceability?.top_k_paths?.[0]);
const activeEventTitle = computed(() => eventTitle(activeEvent.value));
const probabilityRows = computed(() =>
  Object.entries(activeEvent.value?.abnormal_identification?.multilabel_probability || {}).sort((a, b) => b[1] - a[1]),
);
const warningRows = computed(() =>
  [...events.value].sort(
    (a, b) => Number(b.risk_warning?.risk_probability || 0) - Number(a.risk_warning?.risk_probability || 0),
  ),
);
const basisCount = computed(() => {
  const graph = seed.value?.knowledge_graph;
  return Number(graph?.summary.node_count || 0) + Number(graph?.summary.edge_count || 0);
});
const kgPreviewNodes = computed(() => (seed.value?.knowledge_graph?.nodes || []).slice(0, 10));
const kgPreviewEdges = computed(() => (seed.value?.knowledge_graph?.edges || []).slice(0, 8));
const kgDisambiguation = computed(() => seed.value?.knowledge_graph?.disambiguation);
const kgDisambiguationStats = computed(
  () =>
    seed.value?.knowledge_graph?.summary.entity_disambiguation ||
    kgDisambiguation.value || {
      node_merge_count: 0,
      edge_merge_count: 0,
      rule_count: 0,
    },
);
const kgMergedNodes = computed(() => (kgDisambiguation.value?.top_merged_nodes || []).slice(0, 6));
const kgFusionSummary = computed(() => activeEvent.value?.kg_fusion || activeEvidence.value?.kg_fusion_summary);
const kgMissingLinks = computed(() => kgEventSubgraph.value?.missing_links || []);
const kgNodeTypeOptions = computed(() => {
  const nodes = seed.value?.knowledge_graph?.nodes || [];
  return ['all', ...new Set(nodes.map((node) => node.entity_type).filter(Boolean))];
});
const kgRelationTypeOptions = computed(() => {
  const edges = seed.value?.knowledge_graph?.edges || [];
  return ['all', ...new Set(edges.map((edge) => edge.relation_type).filter(Boolean))];
});
const kgVisibleGraph = computed(() => {
  const graph = seed.value?.knowledge_graph;
  const currentSubgraph = kgGraphScope.value === 'current' ? kgEventSubgraph.value : undefined;
  const sourceNodes = currentSubgraph?.nodes || graph?.nodes || [];
  const sourceEdges = currentSubgraph?.edges || graph?.edges || [];
  const degree = new Map<string, number>();
  for (const edge of sourceEdges) {
    degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
  }

  const query = kgGraphQuery.value.trim().toLowerCase();
  let visibleIds = new Set<string>();
  if (query) {
    for (const node of sourceNodes) {
      const haystack = `${node.id} ${node.label} ${node.entity_type} ${(node.aliases || []).join(' ')}`.toLowerCase();
      if (haystack.includes(query)) visibleIds.add(node.id);
    }
    for (const edge of sourceEdges) {
      const haystack = `${edge.source} ${edge.target} ${edge.relation_type} ${edge.label || ''}`.toLowerCase();
      if (haystack.includes(query)) {
        visibleIds.add(edge.source);
        visibleIds.add(edge.target);
      }
    }
    visibleIds = kgExpandNeighborIds(visibleIds, sourceEdges, 1);
  } else if (kgGraphScope.value === 'current') {
    visibleIds = kgExpandNeighborIds(currentKgFocusIds(sourceNodes), sourceEdges, 1);
  } else if (kgGraphScope.value === 'process') {
    visibleIds = new Set(
      sourceNodes
        .filter((node) => ['process_step', 'variable_group', 'defect_mechanism', 'correction_action'].includes(node.entity_type))
        .map((node) => node.id),
    );
  } else if (kgGraphScope.value === 'evidence') {
    visibleIds = new Set(
      [...sourceNodes]
        .sort(
          (a, b) =>
            (Number(b.evidence_count || 1) + Number(b.confidence || 0) * 3 + (degree.get(b.id) || 0)) -
            (Number(a.evidence_count || 1) + Number(a.confidence || 0) * 3 + (degree.get(a.id) || 0)),
        )
        .slice(0, 36)
        .map((node) => node.id),
    );
    visibleIds = kgExpandNeighborIds(visibleIds, sourceEdges, 1);
  } else {
    visibleIds = new Set(sourceNodes.map((node) => node.id));
  }

  if (!visibleIds.size) {
    visibleIds = new Set(sourceNodes.slice(0, 40).map((node) => node.id));
  }

  let visibleEdges = sourceEdges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target));
  if (kgRelationTypeFilter.value !== 'all') {
    visibleEdges = visibleEdges.filter((edge) => edge.relation_type === kgRelationTypeFilter.value);
    const edgeNodeIds = new Set<string>();
    for (const edge of visibleEdges) {
      edgeNodeIds.add(edge.source);
      edgeNodeIds.add(edge.target);
    }
    visibleIds = new Set([...visibleIds].filter((id) => edgeNodeIds.has(id)));
  }
  if (kgNodeTypeFilter.value !== 'all') {
    visibleIds = new Set(
      sourceNodes
        .filter((node) => visibleIds.has(node.id) && node.entity_type === kgNodeTypeFilter.value)
        .map((node) => node.id),
    );
    visibleEdges = visibleEdges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target));
  }
  if (visibleIds.size > 58 && kgGraphScope.value !== 'all') {
    const keep = new Set(
      [...visibleIds]
        .sort((a, b) => (degree.get(b) || 0) - (degree.get(a) || 0))
        .slice(0, 58),
    );
    visibleIds = keep;
  }

  const selectedId = selectedKgNodeId.value && visibleIds.has(selectedKgNodeId.value) ? selectedKgNodeId.value : '';
  const hoveredId = hoveredKgNodeId.value && visibleIds.has(hoveredKgNodeId.value) ? hoveredKgNodeId.value : '';
  const focusId = hoveredId || selectedId;
  const relatedIds = new Set<string>();
  if (focusId) {
    for (const edge of sourceEdges) {
      if (edge.source === focusId) relatedIds.add(edge.target);
      if (edge.target === focusId) relatedIds.add(edge.source);
    }
  }

  const rawNodes = sourceNodes.filter((node) => visibleIds.has(node.id));
  const positioned = kgLayoutNodes(rawNodes, sourceEdges, degree, selectedId, hoveredId, relatedIds);
  const nodeMap = new Map(positioned.map((node) => [node.id, node]));
  const edges = visibleEdges
    .filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target))
    .map((edge) => {
      const sourceNode = nodeMap.get(edge.source)!;
      const targetNode = nodeMap.get(edge.target)!;
      const active = Boolean(focusId && (edge.source === focusId || edge.target === focusId));
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceLabel: sourceNode.label,
        targetLabel: targetNode.label,
        type: edge.relation_type,
        confidence: Number(edge.confidence || 0),
        active,
        sourceNode,
        targetNode,
      };
    });

  return { nodes: positioned, edges };
});
const kgGraphTransform = computed(() => {
  const view = kgGraphView.value;
  return `translate(${view.x}, ${view.y}) scale(${view.k})`;
});
const kgSelectedNode = computed(() => {
  if (!selectedKgNodeId.value) return undefined;
  return kgVisibleGraph.value.nodes.find((node) => node.id === selectedKgNodeId.value);
});
const kgSelectedRelations = computed(() => {
  const node = kgSelectedNode.value;
  if (!node) return [];
  return kgVisibleGraph.value.edges.filter((edge) => edge.source === node.id || edge.target === node.id);
});
const candidateValidationRows = computed(() => [
  ...(candidateValidation.value?.entity_results || []),
  ...(candidateValidation.value?.relation_results || []),
]);
const candidateReviewSummary = computed(() => {
  const summary = candidateValidation.value?.summary;
  return [
    { title: '建议合并', value: summary?.suggested_merge_count || 0, note: '重复或别名知识，累积证据' },
    { title: '建议新建', value: summary?.suggested_new_count || 0, note: '未命中旧图谱，可作为新知识' },
    { title: '需要复核', value: summary?.review_required_count || 0, note: '存在重叠或粒度差异' },
    { title: '冲突拦截', value: summary?.conflict_count || 0, note: '存在方向、类型或语义冲突' },
  ];
});
const kgVersionAssets = computed(() => [
  {
    name: '实时系统图谱',
    type: 'JSON',
    status: String(kgVersions.value?.current_version?.status || '已加载'),
    detail: `${seed.value?.knowledge_graph?.summary.node_count || 0} 个实体 / ${seed.value?.knowledge_graph?.summary.edge_count || 0} 条关系`,
  },
  {
    name: 'RAG 抽取图谱',
    type: 'knowledge_graph.json',
    status: '待同步校验',
    detail: '检测到知识模型产物目录，需后端完成文件读取、清洗和版本发布',
  },
  {
    name: '机制边特征',
    type: 'mechanism_edge_features.csv',
    status: '后端归档',
    detail: '大体量边特征不直接进前端，作为模型服务和审计下载使用',
  },
  {
    name: '复盘入图候选',
    type: 'case-ingest',
    status: caseIngestResult.value ? '待人工审核' : `${kgVersions.value?.recent_actions?.length || 0} 条治理记录`,
    detail: caseIngestResult.value
      ? `${caseIngestResult.value.candidate_entities.length} 个实体 / ${caseIngestResult.value.candidate_relations.length} 条关系`
      : '现场复核确认后生成候选实体、关系和证据来源',
  },
]);
const kgGovernanceFlow = [
  { title: '抽取暂存', note: 'RAG/文本抽取结果先进入候选区，不直接覆盖生产图谱' },
  { title: '人工审核', note: '确认实体、关系、证据片段、置信度和适用工序' },
  { title: '版本发布', note: '发布为可追溯图谱版本，并保留原始文件与变更记录' },
  { title: '模型引用', note: '预警和溯源模型只引用已发布版本，避免未审知识影响判断' },
] as const;
const selectedStepLabel = computed(() => {
  const step = (activeEvent.value?.process_status || seed.value?.process_steps || []).find((item) => item.id === selectedStep.value);
  return step?.name || '全流程';
});
const evidenceConfidence = computed(() => {
  const sources = topPath.value?.evidence_sources || [];
  if (!sources.length) return 0;
  return sources.reduce((sum, item) => sum + Number(item.confidence || 0), 0) / sources.length;
});
const primaryClass = computed(() => {
  const classKey = activeEvent.value?.abnormal_identification?.primary_abnormal_class || probabilityRows.value[0]?.[0] || '';
  return displayLabel(classKey);
});
const cascadeMetrics = computed(() => {
  const metrics = cascadeModel.value?.metrics || {};
  return [
    {
      key: 'binary',
      displayTitle: '预警可信度',
      title: '异常预警',
      value: Number(metrics.binary_test?.macro_f1 || 0),
      level: scoreLevel(Number(metrics.binary_test?.macro_f1 || 0)),
      processNote: `异常捕捉能力${capabilityLevel(Number(metrics.binary_test?.pr_auc || 0))}`,
      raw: `模型复核值 ${fmt(metrics.binary_test?.macro_f1 as number | undefined)} / 捕捉值 ${fmt(metrics.binary_test?.pr_auc as number | undefined)}`,
      note: `PR-AUC ${fmt(metrics.binary_test?.pr_auc as number | undefined)}`,
    },
    {
      key: 'multiclass',
      displayTitle: '异常种类判断可靠度',
      title: '异常种类判断',
      value: Number(metrics.multiclass_test?.macro_f1 || 0),
      level: scoreLevel(Number(metrics.multiclass_test?.macro_f1 || 0)),
      processNote: `类别均衡性${capabilityLevel(Number(metrics.multiclass_test?.balanced_accuracy || 0))}`,
      raw: `模型复核值 ${fmt(metrics.multiclass_test?.macro_f1 as number | undefined)} / 均衡值 ${fmt(metrics.multiclass_test?.balanced_accuracy as number | undefined)}`,
      note: `平衡准确率 ${fmt(metrics.multiclass_test?.balanced_accuracy as number | undefined)}`,
    },
    {
      key: 'multilabel',
      displayTitle: '关联异常提示稳定性',
      title: '关联异常提示',
      value: Number(metrics.multilabel_test?.macro_f1 || 0),
      level: scoreLevel(Number(metrics.multilabel_test?.macro_f1 || 0)),
      processNote: `误报控制${errorControlLevel(Number(metrics.multilabel_test?.hamming_loss || 0))}`,
      raw: `模型复核值 ${fmt(metrics.multilabel_test?.macro_f1 as number | undefined)} / 错标率 ${fmt(metrics.multilabel_test?.hamming_loss as number | undefined)}`,
      note: `Hamming ${fmt(metrics.multilabel_test?.hamming_loss as number | undefined)}`,
    },
  ];
});
const cascadePipeline = computed(() => cascadeModel.value?.pipeline || []);
const topModelFeatures = computed(() => cascadeModel.value?.features?.top_global_features?.slice(0, 6) || []);
const abnormalParameterRows = computed(() =>
  topModelFeatures.value.map((feature, index) => ({
    key: String(feature.feature || `parameter-${index}`),
    label: evidenceLabel(String(feature.feature || '异常相关参数')),
    group: evidenceLabel(String(feature.feature_group || '相关信号组')),
    priority: index + 1,
  })),
);
const modelDatasetStats = computed(() => cascadeModel.value?.dataset || {});
const modelGatePolicy = computed(() => cascadeModel.value?.gate_policy);
const gatePolicyNormalRule = computed(() =>
  businessPolicyRule(
    String(modelGatePolicy.value?.normal_rule || ''),
    '判断为无品质异常时，系统只保留监测记录，不触发现场处置。',
  ),
);
const gatePolicyAbnormalRule = computed(() =>
  businessPolicyRule(
    String(modelGatePolicy.value?.abnormal_rule || ''),
    '判断为异常时，系统进入异常种类判断、关联异常提示和原因链路复核。',
  ),
);
const inferenceSteps = computed(() => [
  {
    key: 'window',
    title: '生产事件',
    value: lineName(activeEvent.value?.line_id),
    note: activeEvent.value?.timestamp || '实时生产事件',
    confidence: activeEvent.value ? 1 : 0,
  },
  {
    key: 'risk',
    title: '质量预警',
    value: riskLevelName(activeEvent.value?.risk_warning?.risk_level),
    note: `概率 ${fmt(activeEvent.value?.risk_warning?.risk_probability)}`,
    confidence: Number(activeEvent.value?.risk_warning?.risk_probability || 0),
  },
  {
    key: 'identify',
    title: '异常类型',
    value: primaryClass.value,
    note: `置信 ${fmt(probabilityRows.value[0]?.[1])}`,
    confidence: Number(probabilityRows.value[0]?.[1] || 0),
  },
  {
    key: 'trace',
    title: '候选原因',
    value: displayLabel(topPath.value?.defect_mechanism || ''),
    note: fieldLabel(topPath.value?.equipment_zone || selectedStepLabel.value),
    confidence: Number(topPath.value?.final_score || topPath.value?.path_score || 0),
  },
  {
    key: 'evidence',
    title: '复核依据',
    value: `${topPath.value?.evidence_sources?.length || 0} 条依据`,
    note: `平均置信 ${fmt(evidenceConfidence.value)}`,
    confidence: evidenceConfidence.value,
  },
  {
    key: 'action',
    title: '处置建议',
    value: activeEvent.value?.recommendation?.recommended_checks?.[0] || '待复核',
    note: riskActionText.value,
    confidence: activeEvent.value ? 0.86 : 0,
  },
]);
const riskActionText = computed(() => {
  const level = activeEvent.value?.risk_warning?.risk_level;
  if (level === 'high') return '立即复核并执行处置';
  if (level === 'medium') return '班组确认并持续观察';
  return '保持监控';
});

onMounted(async () => {
  seed.value = await getSteelRealtimeSeed();
  events.value = seed.value.events || [];
  activeEvent.value = events.value[0];
  await refreshActiveEvidence();
  await refreshKgVersions();
  await refreshModelArtifacts();
  await searchBasis();
  log('生产系统已接入');
});

onBeforeUnmount(() => {
  stopStream();
});

function fmt(value?: number | string | null) {
  return typeof value === 'number' ? value.toFixed(3) : value || '-';
}

function scoreLevel(value?: number | null) {
  const score = Number(value || 0);
  if (score >= 0.9) return '高';
  if (score >= 0.8) return '较高';
  if (score >= 0.7) return '中等';
  if (score > 0) return '需关注';
  return '待评估';
}

function capabilityLevel(value?: number | null) {
  const score = Number(value || 0);
  if (score >= 0.95) return '很强';
  if (score >= 0.9) return '强';
  if (score >= 0.8) return '较强';
  if (score > 0) return '需复核';
  return '待评估';
}

function errorControlLevel(value?: number | null) {
  const loss = Number(value || 0);
  if (loss <= 0.08) return '好';
  if (loss <= 0.12) return '较好';
  if (loss <= 0.2) return '一般';
  return '需关注';
}

function entries(value?: Record<string, unknown>) {
  return Object.entries(value || {});
}

function stageDisplayName(stage: { stage?: string; name?: string }) {
  const map: Record<string, string> = {
    binary_warning: '异常预警',
    multiclass_identification: '异常种类判断',
    multilabel_companion: '关联异常提示',
    gated_traceability: '溯源证据复核',
  };
  return map[String(stage.stage || '')] || businessStageText(stage.name || '质量模型节点');
}

function stageOutputName(stage: { stage?: string; output?: string }) {
  const map: Record<string, string> = {
    binary_warning: '预警概率与风险等级',
    multiclass_identification: '主要异常种类',
    multilabel_companion: '可能并发的异常线索',
    gated_traceability: '候选原因链路与证据',
  };
  return map[String(stage.stage || '')] || businessStageText(stage.output || '模型输出');
}

function businessStageText(value: string) {
  return value
    .replace(/二分类/g, '异常预警')
    .replace(/多分类/g, '异常种类判断')
    .replace(/主异常分类/g, '异常种类判断')
    .replace(/主类识别/g, '异常种类判断')
    .replace(/多标签/g, '关联异常提示')
    .replace(/伴随异常识别/g, '关联异常提示')
    .replace(/级联模型/g, '质量模型')
    .replace(/门控/g, '预警判定');
}

function businessPolicyRule(value: string, fallback: string) {
  return value ? businessStageText(value) : fallback;
}

function displayLabel(key: string) {
  return formatSteelTerm(key, seed.value?.display_labels);
}

function textValue(value: unknown) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toFixed(3);
  return value == null ? '-' : String(value);
}

function fieldLabel(value: unknown) {
  return formatSteelTerm(value, seed.value?.display_labels);
}

function riskLevelName(level?: string) {
  return formatRiskLevelName(level);
}

function lineName(lineId?: string) {
  return formatLineName(lineId);
}

function sequenceName(sequence?: number) {
  return formatSequenceName(sequence);
}

function eventTitle(event?: SteelRealtimeEvent) {
  return formatEventDisplayTitle(event, seed.value?.display_labels) || formatEventTitle(event, seed.value?.display_labels);
}

function displayGroups(event?: SteelRealtimeEvent) {
  const groups = event?.abnormal_identification?.display_groups?.length
    ? event.abnormal_identification.display_groups
    : event?.abnormal_identification?.predicted_abnormal_groups || [];
  return groups.map((item) => displayLabel(item)).filter(Boolean);
}

function evidenceLabel(key: string) {
  const map: Record<string, string> = {
    risk_probability: '风险概率',
    primary_feature: '关键变量',
    variable_group: '信号组',
    window_scope: '时间窗口',
    mechanism: '异常机理',
    equipment_zone: '工序位置',
    graph_prior: '经验置信',
    graph_relation_score: '图谱关系评分',
    path_library_score: '历史路径评分',
    path_library_match: '历史链路匹配',
    path_library_event_count: '历史命中次数',
    score_model: '评分模型',
    macro_f1: '综合判别稳定性',
    pr_auc: '异常捕捉能力',
    balanced_accuracy: '平衡准确率',
    hamming_loss: '错标率',
    normal_gate_policy: '正常门控策略',
    binary_abnormal_probability: '异常概率',
    cascade_main_class_score: '最终主类得分',
    kept_count: '保留特征数',
    original_count: '原始特征数',
    dropped_correlated_count: '相关性裁剪特征数',
  };
  return map[key] || formatSteelTerm(key, seed.value?.display_labels);
}

function evidenceValue(value: unknown): string {
  if (Array.isArray(value)) return value.map((item) => evidenceValue(item)).join('、');
  if (typeof value === 'number') return value.toFixed(3);
  if (typeof value === 'boolean') return value ? '是' : '否';
  if (typeof value === 'string') {
    const map: Record<string, string> = {
      kg_evidence_fusion_v2: '知识图谱证据融合评分',
    };
    return map[value] || fieldLabel(value);
  }
  return value == null ? '-' : JSON.stringify(value);
}

function evidenceText(value: unknown) {
  let text = textValue(value);
  for (const key of Object.keys(STEEL_TERM_LABELS).sort((a, b) => b.length - a.length)) {
    text = text.split(key).join(fieldLabel(key));
  }
  return text;
}

function relationEndpointLabel(value: string) {
  const raw = String(value || '');
  const [, id = raw] = raw.split('::');
  return fieldLabel(id);
}

function sourceTypeLabel(value?: string) {
  return formatSourceType(value);
}

function entityTypeLabel(value?: string) {
  return formatEntityType(value);
}

function relationTypeLabel(value?: string) {
  const map: Record<string, string> = {
    SUPPORTS_MECHANISM: '变量组支持异常机理',
    SUGGESTS_ACTION: '机理建议处置',
    PRECEDES_PROCESS: '工艺顺序',
    ZONE_BELONGS_TO_PROCESS: '区域归属工序',
    HAS_STAT_FEATURE: '基础变量生成窗口指标',
    SUPPORTS_PROCESS_STATE: '变量组支持工艺状态',
    STATE_INDICATES_MECHANISM: '工艺状态指向异常机理',
    CAUSES_QUALITY_RISK: '机理对应质量异常',
    SUPPORTED_BY_TEXT: '文本证据支持机理',
    SUPPORTED_BY_CASE: '历史案例支持机理',
    CASE_HAS_SIGNAL: '历史案例包含关键信号',
  };
  return (value && map[value]) || formatRelationType(value);
}

function reviewStatusLabel(value?: string) {
  return formatReviewStatus(value);
}

function candidateStatusLabel(value?: string) {
  const map: Record<string, string> = {
    candidate_conflict: '存在冲突',
    candidate_review_required: '需要复核',
    candidate_duplicate_or_alias: '建议合并',
    candidate_publish_ready_after_review: '待审核发布',
  };
  return (value && map[value]) || '等待候选知识';
}

function knowledgeTypeLabel(value?: string) {
  const map: Record<string, string> = {
    abnormal_class: '异常类型',
    traceability_path: '原因链路',
    graph_relation: '图谱关系',
    event_path: '事件样本',
    display_label: '类别解释',
  };
  return (value && map[value]) || fieldLabel(value || '生产依据');
}

function basisResultKey(item: KnowledgeItem) {
  return `${item.type || 'basis'}::${item.id || item.key || item.title}`;
}

function normalizeBasisResults(items: KnowledgeItem[]) {
  const seen = new Set<string>();
  const rows: KnowledgeItem[] = [];
  for (const item of items) {
    const key = basisResultKey(item);
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push(item);
  }
  return rows.slice(0, 12);
}

function kgIdVariants(raw?: unknown) {
  const value = String(raw || '').trim();
  if (!value) return [];
  const [, key = value] = value.split('::');
  return [
    value,
    `base_variable::${key}`,
    `feature::${key}`,
    `variable_group::${key}`,
    `process::${key}`,
    `equipment_zone::${key}`,
    `process_state::${key}`,
    `mechanism::${key}`,
    `quality_class::${key}`,
    `text::${key}`,
    `case::${key}`,
    `action::${key}`,
  ];
}

function currentKgFocusIds(nodes: KnowledgeEntity[]) {
  const nodeIds = new Set(nodes.map((node) => node.id));
  const raw = new Set<string>();
  for (const id of activeEvent.value?.kg_fusion?.focus_node_ids || []) {
    raw.add(String(id || ''));
  }
  for (const id of kgEventSubgraph.value?.focus_node_ids || []) {
    raw.add(String(id || ''));
  }
  const path = topPath.value;
  const canonical = (path?.canonical_path || {}) as Record<string, unknown>;
  for (const key of [
    'base_variable_id',
    'feature_id',
    'variable_group_id',
    'equipment_zone_id',
    'process_state_id',
    'mechanism_id',
    'quality_class_id',
    'feature',
    'variable_group',
    'equipment_zone',
    'defect_mechanism',
    'event_target',
  ]) {
    raw.add(String(canonical[key] || (path as unknown as Record<string, unknown> | undefined)?.[key] || ''));
  }
  const result = new Set<string>();
  for (const value of raw) {
    for (const variant of kgIdVariants(value)) {
      if (nodeIds.has(variant)) result.add(variant);
      if (variant.startsWith('equipment_zone::')) {
        const processId = variant.replace('equipment_zone::', 'process::');
        if (nodeIds.has(processId)) result.add(processId);
      }
    }
  }
  return result;
}

function kgExpandNeighborIds(ids: Set<string>, edges: KnowledgeRelation[], depth = 1) {
  const expanded = new Set(ids);
  for (let i = 0; i < depth; i += 1) {
    for (const edge of edges) {
      if (expanded.has(edge.source)) expanded.add(edge.target);
      if (expanded.has(edge.target)) expanded.add(edge.source);
    }
  }
  return expanded;
}

function kgTypeRank(type?: string) {
  const ranks: Record<string, number> = {
    base_variable: 0,
    feature: 0,
    window_feature: 0,
    variable_group: 1,
    process_step: 2,
    equipment_zone: 2,
    process_state: 3,
    defect_mechanism: 3,
    quality_class: 4,
    text_evidence: 4,
    reviewed_quality_case: 4,
    correction_action: 4,
    action: 4,
  };
  return ranks[type || ''] ?? 2;
}

function kgHash(value: string) {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) hash = (hash * 31 + value.charCodeAt(i)) % 997;
  return hash;
}

function shortKgLabel(value: string, max = 12) {
  const text = fieldLabel(value || '');
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function kgLayoutNodes(
  nodes: KnowledgeEntity[],
  edges: KnowledgeRelation[],
  degree: Map<string, number>,
  selectedId: string,
  hoveredId: string,
  relatedIds: Set<string>,
): KgGraphNode[] {
  const nodeIds = new Set(nodes.map((node) => node.id));
  const visibleEdges = edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target));
  const centers: Record<number, KgPoint> = {
    0: { x: 250, y: 230 },
    1: { x: 330, y: 230 },
    2: { x: 480, y: 230 },
    3: { x: 655, y: 230 },
    4: { x: 780, y: 230 },
  };
  const simulation = nodes.map((node, index) => {
    const rank = kgTypeRank(node.entity_type);
    const center = centers[rank] || centers[2];
    const manual = kgNodePositions.value[node.id];
    const nodeDegree = degree.get(node.id) || 0;
    const angle = ((index * 137.5 + kgHash(node.id)) % 360) * (Math.PI / 180);
    const spread = 52 + (kgHash(node.id) % 92);
    return {
      node,
      fixed: Boolean(manual),
      x: manual?.x ?? center.x + Math.cos(angle) * spread,
      y: manual?.y ?? center.y + Math.sin(angle) * spread * 0.72,
      vx: 0,
      vy: 0,
      degree: nodeDegree,
      radius: Math.min(28, 11 + Math.sqrt(nodeDegree + Number(node.evidence_count || 1)) * 2.3),
    };
  });
  const byId = new Map(simulation.map((item) => [item.node.id, item]));

  for (let tick = 0; tick < 96; tick += 1) {
    const cooling = 1 - tick / 120;
    for (let i = 0; i < simulation.length; i += 1) {
      const a = simulation[i];
      for (let j = i + 1; j < simulation.length; j += 1) {
        const b = simulation[j];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distSq = dx * dx + dy * dy;
        if (distSq < 0.01) {
          dx = ((kgHash(`${a.node.id}:${b.node.id}`) % 11) - 5) || 1;
          dy = ((kgHash(`${b.node.id}:${a.node.id}`) % 11) - 5) || 1;
          distSq = dx * dx + dy * dy;
        }
        const dist = Math.sqrt(distSq);
        const desired = a.radius + b.radius + 38;
        const repel = Math.min(2.4, (desired * desired) / Math.max(80, distSq)) * cooling;
        const nx = dx / dist;
        const ny = dy / dist;
        if (!a.fixed) {
          a.vx -= nx * repel;
          a.vy -= ny * repel;
        }
        if (!b.fixed) {
          b.vx += nx * repel;
          b.vy += ny * repel;
        }
      }
    }

    for (const edge of visibleEdges) {
      const a = byId.get(edge.source);
      const b = byId.get(edge.target);
      if (!a || !b || a === b) continue;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
      const desired = 118 + Math.abs(kgTypeRank(a.node.entity_type) - kgTypeRank(b.node.entity_type)) * 18;
      const spring = (dist - desired) * 0.018 * cooling;
      const nx = dx / dist;
      const ny = dy / dist;
      if (!a.fixed) {
        a.vx += nx * spring;
        a.vy += ny * spring;
      }
      if (!b.fixed) {
        b.vx -= nx * spring;
        b.vy -= ny * spring;
      }
    }

    for (const item of simulation) {
      const center = centers[kgTypeRank(item.node.entity_type)] || centers[2];
      if (!item.fixed) {
        item.vx += (center.x - item.x) * 0.008 * cooling;
        item.vy += (center.y - item.y) * 0.008 * cooling;
        item.x += item.vx;
        item.y += item.vy;
      }
      item.vx *= 0.72;
      item.vy *= 0.72;
      item.x = Math.max(46, Math.min(914, item.x));
      item.y = Math.max(40, Math.min(420, item.y));
    }
  }

  return simulation
    .map((item) => {
      const node = item.node;
      const fullLabel = fieldLabel(node.label || node.id);
      const selected = node.id === selectedId;
      const hovered = node.id === hoveredId;
      const related = relatedIds.has(node.id);
      const expandedLabel =
        kgShowLabels.value &&
        node.entity_type !== 'feature' &&
        (item.degree >= 3 || node.entity_type === 'variable_group' || node.entity_type === 'defect_mechanism');
      const showLabel =
        selected ||
        hovered ||
        node.entity_type === 'process_step' ||
        expandedLabel ||
        (node.entity_type === 'defect_mechanism' && item.degree >= 2) ||
        (related && item.degree >= 5);
      const displayLabel = shortKgLabel(fullLabel, showLabel && (selected || hovered) ? 18 : 9);
      return {
        id: node.id,
        label: displayLabel,
        fullLabel,
        type: node.entity_type,
        typeLabel: entityTypeLabel(node.entity_type),
        confidence: Number(node.confidence || 0),
        reviewStatus: node.review_status,
        evidenceCount: node.evidence_count,
        sourceType: node.source_type,
        aliases: node.aliases || [],
        degree: item.degree,
        x: Math.round(item.x * 10) / 10,
        y: Math.round(item.y * 10) / 10,
        radius: item.radius,
        labelWidth: Math.min(168, Math.max(58, displayLabel.length * 12 + 18)),
        selected,
        related,
        hovered,
        showLabel,
      };
    })
    .sort((a, b) => Number(a.selected || a.related) - Number(b.selected || b.related) || a.radius - b.radius);
}

function kgEdgePath(edge: KgGraphEdge) {
  const { sourceNode, targetNode } = edge;
  if (sourceNode.id === targetNode.id) {
    const x = sourceNode.x;
    const y = sourceNode.y;
    return `M ${x + 14} ${y - 6} C ${x + 54} ${y - 48}, ${x + 82} ${y + 36}, ${x + 16} ${y + 12}`;
  }
  const sx = sourceNode.x;
  const sy = sourceNode.y;
  const tx = targetNode.x;
  const ty = targetNode.y;
  const mx = (sx + tx) / 2;
  const my = (sy + ty) / 2;
  const curve = Math.max(-36, Math.min(36, (ty - sy) * 0.2));
  return `M ${sx} ${sy} Q ${mx} ${my - curve} ${tx} ${ty}`;
}

function selectKgNode(nodeId: string) {
  selectedKgNodeId.value = nodeId;
}

function setKgGraphScope(scope: KgGraphScope) {
  kgGraphScope.value = scope;
  selectedKgNodeId.value = '';
  hoveredKgNodeId.value = '';
  kgNodePositions.value = {};
  kgGraphView.value = { x: 0, y: 0, k: 1 };
}

function resetKgGraphView() {
  kgGraphQuery.value = '';
  kgNodeTypeFilter.value = 'all';
  kgRelationTypeFilter.value = 'all';
  selectedKgNodeId.value = '';
  hoveredKgNodeId.value = '';
  kgNodePositions.value = {};
  kgGraphView.value = { x: 0, y: 0, k: 1 };
}

function kgGraphPointFromEvent(event: PointerEvent): KgPoint {
  const svg = event.currentTarget as SVGSVGElement;
  const rect = svg.getBoundingClientRect();
  return {
    x: ((event.clientX - rect.left) / Math.max(rect.width, 1)) * 960,
    y: ((event.clientY - rect.top) / Math.max(rect.height, 1)) * 460,
  };
}

function kgGraphLocalPoint(event: PointerEvent): KgPoint {
  const point = kgGraphPointFromEvent(event);
  const view = kgGraphView.value;
  return {
    x: (point.x - view.x) / view.k,
    y: (point.y - view.y) / view.k,
  };
}

function zoomKgGraph(factor: number, center: KgPoint = { x: 480, y: 230 }) {
  const current = kgGraphView.value;
  const nextK = Math.max(0.55, Math.min(2.8, current.k * factor));
  const ratio = nextK / current.k;
  kgGraphView.value = {
    k: nextK,
    x: center.x - (center.x - current.x) * ratio,
    y: center.y - (center.y - current.y) * ratio,
  };
}

function fitKgGraph() {
  const nodes = kgVisibleGraph.value.nodes;
  if (!nodes.length) {
    kgGraphView.value = { x: 0, y: 0, k: 1 };
    return;
  }
  const minX = Math.min(...nodes.map((node) => node.x - node.radius));
  const maxX = Math.max(...nodes.map((node) => node.x + node.radius));
  const minY = Math.min(...nodes.map((node) => node.y - node.radius));
  const maxY = Math.max(...nodes.map((node) => node.y + node.radius));
  const width = Math.max(1, maxX - minX);
  const height = Math.max(1, maxY - minY);
  const scale = Math.max(0.65, Math.min(1.85, Math.min(850 / width, 370 / height)));
  kgGraphView.value = {
    k: scale,
    x: 480 - ((minX + maxX) / 2) * scale,
    y: 230 - ((minY + maxY) / 2) * scale,
  };
}

function onKgGraphWheel(event: WheelEvent) {
  const point = kgGraphPointFromEvent(event as unknown as PointerEvent);
  zoomKgGraph(event.deltaY > 0 ? 0.88 : 1.14, point);
}

function onKgGraphPanStart(event: PointerEvent) {
  const point = kgGraphPointFromEvent(event);
  kgPanStart.value = { x: point.x, y: point.y, view: { ...kgGraphView.value } };
}

function onKgNodePointerDown(nodeId: string, event: PointerEvent) {
  selectedKgNodeId.value = nodeId;
  kgDraggedNodeId.value = nodeId;
  kgPanStart.value = undefined;
  event.preventDefault();
}

function onKgGraphPointerMove(event: PointerEvent) {
  if (kgDraggedNodeId.value) {
    const point = kgGraphLocalPoint(event);
    kgNodePositions.value = {
      ...kgNodePositions.value,
      [kgDraggedNodeId.value]: {
        x: Math.max(40, Math.min(920, point.x)),
        y: Math.max(38, Math.min(422, point.y)),
      },
    };
    return;
  }
  if (kgPanStart.value) {
    const point = kgGraphPointFromEvent(event);
    kgGraphView.value = {
      ...kgPanStart.value.view,
      x: kgPanStart.value.view.x + point.x - kgPanStart.value.x,
      y: kgPanStart.value.view.y + point.y - kgPanStart.value.y,
    };
  }
}

function stopKgNodeDrag() {
  kgDraggedNodeId.value = '';
  kgPanStart.value = undefined;
}

function kgNodeDescription(node: KgGraphNode) {
  const aliasText = node.aliases.length ? `别名：${node.aliases.map(fieldLabel).slice(0, 4).join('、')}。` : '';
  const sourceText = node.sourceType ? `来源：${sourceTypeLabel(node.sourceType)}。` : '';
  return `${entityTypeLabel(node.type)}节点，关联 ${node.degree} 条关系。${sourceText}${aliasText}`;
}

function goModule(module: ModuleKey) {
  activeModule.value = module;
}

function log(message: string) {
  operationLog.value.push(`${new Date().toLocaleTimeString()} ${message}`);
}

function selectStep(stepId: string) {
  selectedStep.value = stepId;
  log(`关注工序切换为 ${selectedStepLabel.value}`);
}

function toggleStream() {
  if (running.value) {
    running.value = false;
    stopStream();
    log('实时数据流已暂停');
    return;
  }
  running.value = true;
  try {
    eventSource = connectRealtimeStream(cursor.value, applyStreamPayload);
    eventSource.onerror = () => {
      eventSource?.close();
      eventSource = undefined;
      if (!timer) timer = window.setInterval(loadNextEvent, 1600);
    };
  } catch {
    timer = window.setInterval(loadNextEvent, 1600);
  }
  log('实时数据流已启动');
}

function stopStream() {
  if (timer) window.clearInterval(timer);
  timer = undefined;
  eventSource?.close();
  eventSource = undefined;
}

async function applyStreamPayload(payload: { cursor: number; event: SteelRealtimeEvent }) {
  cursor.value = payload.cursor;
  activeEvent.value = payload.event;
  await refreshActiveEvidence();
  if (!events.value.find((item) => item.event_id === payload.event.event_id)) {
    events.value.push(payload.event);
  }
}

async function loadNextEvent() {
  const payload = await getNextRealtimeEvent(cursor.value);
  cursor.value = payload.cursor;
  activeEvent.value = payload.event;
  await refreshActiveEvidence();
  if (!events.value.find((item) => item.event_id === payload.event.event_id)) {
    events.value.push(payload.event);
  }
  log(`切换到 ${eventTitle(payload.event)}`);
}

async function selectEvent(eventId: string) {
  activeEvent.value = await getEventDetail(eventId);
  await refreshActiveEvidence();
  log(`选中 ${eventTitle(activeEvent.value)}`);
}

async function refreshActiveEvidence() {
  if (!activeEvent.value?.event_id) return;
  try {
    const [evidence, subgraph] = await Promise.all([
      getKgEvidence(activeEvent.value.event_id),
      getKgEventSubgraph(activeEvent.value.event_id, 1),
    ]);
    activeEvidence.value = evidence;
    kgEventSubgraph.value = subgraph;
  } catch {
    activeEvidence.value = activeEvent.value.traceability?.evidence_package;
    kgEventSubgraph.value = undefined;
  }
}

async function refreshKgVersions() {
  try {
    kgVersions.value = await getKgVersions();
  } catch {
    kgVersions.value = undefined;
  }
}

async function refreshModelArtifacts() {
  try {
    cascadeModel.value = await getCascadeModelSummary();
    const evidence = await getTraceabilityEvidenceRows(12, true);
    cascadeEvidenceRows.value = evidence.rows || [];
    log('质量模型实验产物已接入');
  } catch {
    cascadeEvidenceRows.value = [];
    log('质量模型实验产物暂不可用');
  }
}

async function handleUpload(evt: Event) {
  const input = evt.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const payload = JSON.parse(await file.text()) as Record<string, unknown>;
  const response = await ingestRealtimeEvent(payload);
  activeEvent.value = response.event;
  await refreshActiveEvidence();
  events.value.push(response.event);
  cursor.value = events.value.length;
  log(`接入 ${eventTitle(response.event)}`);
}

async function askPathQuestion() {
  const path = topPath.value;
  try {
    const response = await askAssistantPathQuestion({
      event_id: activeEvent.value?.event_id,
      path_index: 0,
      question: question.value || '解释当前事件',
    });
    answer.value = response.answer;
    const runtime = response.llm_runtime;
    assistantStatus.value = runtime?.status === 'ok'
      ? `LLM 已接入：${runtime.model || '当前模型'}`
      : runtime?.status === 'fallback_after_error'
        ? `LLM 调用失败，已回退本地解释：${runtime.model || '-'}`
        : '未配置 LLM，使用本地解释';
    log('值班助手已生成说明');
  } catch {
    const query = path?.defect_mechanism || path?.variable_group || question.value;
    const knowledge = await searchKnowledge(query || '');
    const evidence = knowledge.items
      .slice(0, 2)
      .map((item) => `${item.title}：${item.content || item.summary || ''}`)
      .join('；');
    answer.value = `问题：${question.value || '解释当前事件'}。当前事件关联 ${displayLabel(path?.defect_mechanism || '')}，优先关注 ${fieldLabel(path?.equipment_zone || selectedStepLabel.value)}，关键变量为 ${fieldLabel(path?.feature || '-')}。${evidence || '暂无匹配生产依据'}。说明：助手只辅助值班表达，最终处置以现场复核为准。`;
    assistantStatus.value = '助手接口不可用，已回退本地解释';
    log('值班助手已回退本地说明');
  }
}

async function searchBasis() {
  const result = await searchKnowledge(basisQuery.value || '');
  basisResults.value = normalizeBasisResults(result.items || []);
  log(`检索生产依据：${basisQuery.value || '全部'}`);
}

async function saveFeedback() {
  const text = feedback.value.trim();
  if (!activeEvent.value?.event_id) {
    knowledgeIngestStatus.value = '请先选择一个异常事件';
    log('请先选择一个异常事件');
    return;
  }
  knowledgeIngestStatus.value = '正在生成入图候选';
  caseIngestResult.value = await createCaseKnowledgeIngest({
    event_id: activeEvent.value.event_id,
    path_index: 0,
    feedback: text,
    review_status: text ? 'pending_manual_review' : 'pending_feedback_completion',
  });
  candidateValidation.value = await validateKnowledgeCandidate(caseIngestResult.value);
  knowledgeIngestStatus.value = `已生成 ${caseIngestResult.value.candidate_entities.length} 个实体、${caseIngestResult.value.candidate_relations.length} 条关系，${candidateValidation.value.recommendation}`;
  log(text ? '复盘知识候选已生成' : '已生成候选，请补充复核反馈后再审核');
}

async function submitKgAction(actionType: 'mark_review_required' | 'request_merge' | 'publish_candidate') {
  if (!kgSelectedNode.value) {
    kgGovernanceStatus.value = '请先选择一个图谱节点';
    return;
  }
  const response = await submitKgGovernanceAction({
    action_type: actionType,
    target_type: 'knowledge_node',
    target_id: kgSelectedNode.value.id,
    decision: actionType === 'publish_candidate' ? 'candidate_publish_requested' : 'pending_review',
    note: `${activeEvent.value?.event_id || 'current-event'} / ${kgSelectedNode.value.fullLabel}`,
  });
  kgGovernanceStatus.value = `${response.status}：${response.next_step}`;
  await refreshKgVersions();
  log(`图谱维护动作：${relationEndpointLabel(kgSelectedNode.value.id)} / ${actionType}`);
}
</script>

<style scoped>
.steel-shell {
  min-height: 100vh;
  color: #e7f0fb;
  background: radial-gradient(circle at 18% 0%, #14375d 0, #07111f 34%, #050b14 100%);
}

.top-title strong {
  display: block;
  margin-bottom: 4px;
  color: #e7f0fb;
  font-size: 16px;
}

.module-tabs small,
.topbar p,
.panel p,
.panel li,
.muted,
.path-library span,
.basis-result-card {
  color: #8ea5bd;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.module-tabs {
  text-align: left;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 72px;
  border-bottom: 1px solid #24405f;
  padding: 0 22px;
  background: rgba(7, 17, 31, 0.78);
  backdrop-filter: blur(10px);
}

.topbar h1 {
  margin: 0;
  font-size: 21px;
}

.topbar p {
  margin: 5px 0 0;
}

.top-status,
.toolbar,
.evidence-chip-row,
.query-row,
.qa-row,
.operation-log {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.status-pill {
  border: 1px solid #315371;
  border-radius: 999px;
  padding: 6px 10px;
  color: #c7d8e9;
  background: #10233d;
}

.status-pill.ok {
  border-color: rgba(48, 209, 128, 0.5);
  color: #a9ffd1;
}

.status-pill.idle {
  color: #f4bc45;
}

.toolbar,
.module-tabs,
.workspace,
.kpi-grid,
.operation-log {
  margin: 16px 18px 0;
}

.toolbar,
.module-tabs {
  border: 1px solid #24405f;
  border-radius: 10px;
  padding: 12px;
  background: rgba(13, 27, 47, 0.88);
}

.module-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.module-tabs button {
  position: relative;
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 13px;
  align-items: center;
  overflow: hidden;
  min-height: 58px;
  border: 1px solid #24405f;
  border-radius: 8px;
  padding: 10px 12px;
  color: #c7d8e9;
  text-align: left;
  background: #071525;
  cursor: pointer;
}

.module-tabs button::before {
  position: absolute;
  inset: 0;
  opacity: 0.18;
  content: '';
  background:
    linear-gradient(90deg, rgba(7, 21, 37, 0.98), rgba(7, 21, 37, 0.72)),
    var(--module-bg);
  background-position: center;
  background-size: cover;
  transition: opacity 0.18s ease;
}

.module-tabs button.active,
.module-tabs button:hover {
  border-color: #27d4ff;
  color: #fff;
  background: rgba(39, 212, 255, 0.1);
}

.module-tabs button.active::before,
.module-tabs button:hover::before {
  opacity: 0.32;
}

.module-tabs b,
.module-tabs small {
  position: relative;
  z-index: 1;
  display: block;
}

.module-tab__thumb {
  position: relative;
  z-index: 1;
  width: 58px;
  height: 58px;
  border: 1px solid rgba(39, 212, 255, 0.24);
  border-radius: 8px;
  object-fit: cover;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.34);
  filter: saturate(1.08) contrast(1.06);
}

.module-tab__copy {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.module-tabs small {
  margin-top: 4px;
  font-size: 12px;
}

button,
.upload {
  border: 1px solid #315371;
  border-radius: 8px;
  padding: 9px 12px;
  color: #e7f0fb;
  background: #10233d;
  cursor: pointer;
}

button.primary,
.primary {
  border-color: #27d4ff;
  color: #03101b;
  font-weight: 700;
  background: linear-gradient(135deg, #2f7dff, #27d4ff);
}

.upload input {
  display: none;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.kpi,
.panel {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(36, 64, 95, 0.9);
  border-radius: 10px;
  padding: 16px;
  background: rgba(13, 27, 47, 0.92);
}

.realtime-chain-card,
.trace-summary-card,
.kg-overview-card,
.kg-search-card,
.kg-library-card,
.kg-history-card,
.kg-ingest-card {
  background-position: center;
  background-size: cover;
}

.realtime-chain-card {
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.96), rgba(7, 17, 31, 0.84)),
    linear-gradient(180deg, rgba(7, 17, 31, 0.68), rgba(5, 11, 20, 0.94)),
    url('/steel_realtime_workshop_bg.png');
}

.trace-summary-card {
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.96), rgba(7, 17, 31, 0.82)),
    linear-gradient(180deg, rgba(7, 17, 31, 0.72), rgba(5, 11, 20, 0.94)),
    url('/steel_trace_path_bg.png');
}

.kg-overview-card,
.kg-search-card,
.kg-library-card,
.kg-history-card,
.kg-ingest-card {
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.96), rgba(7, 17, 31, 0.82)),
    linear-gradient(180deg, rgba(7, 17, 31, 0.68), rgba(5, 11, 20, 0.94)),
    url('/steel_kg_evidence_bg.png');
}

.realtime-chain-card::before,
.trace-summary-card::before,
.kg-overview-card::before,
.kg-search-card::before,
.kg-library-card::before,
.kg-history-card::before,
.kg-ingest-card::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: '';
  background:
    radial-gradient(circle at 78% 20%, rgba(39, 212, 255, 0.12), transparent 28%),
    linear-gradient(90deg, transparent, rgba(39, 212, 255, 0.08), transparent);
}

.realtime-chain-card > *,
.trace-summary-card > *,
.kg-overview-card > *,
.kg-search-card > *,
.kg-library-card > *,
.kg-history-card > *,
.kg-ingest-card > * {
  position: relative;
  z-index: 1;
}

.visual-frame-card {
  display: grid;
  grid-template-columns: minmax(420px, 1.35fr) minmax(300px, 0.75fr);
  gap: 18px;
  align-items: stretch;
  padding: 12px;
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.96), rgba(7, 17, 31, 0.9)),
    #071525;
}

.visual-frame-card__image {
  width: 100%;
  height: 320px;
  border: 1px solid rgba(39, 212, 255, 0.28);
  border-radius: 8px;
  object-fit: cover;
  object-position: center;
}

.visual-frame-card__copy {
  display: flex;
  border: 1px solid rgba(36, 64, 95, 0.9);
  border-radius: 8px;
  padding: 16px;
  flex-direction: column;
  justify-content: center;
  background: rgba(5, 18, 32, 0.78);
}

.visual-frame-card__copy span,
.visual-frame-card__metrics b {
  width: fit-content;
  border: 1px solid rgba(39, 212, 255, 0.36);
  border-radius: 999px;
  padding: 5px 9px;
  color: #a9dfff;
  font-size: 12px;
  background: rgba(39, 212, 255, 0.08);
}

.visual-frame-card__copy h2 {
  margin: 14px 0 8px;
  color: #f0f7ff;
}

.visual-frame-card__copy p {
  margin: 0;
  color: #b8c9da;
  line-height: 1.7;
}

.visual-frame-card__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.visual-asset-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.visual-asset-card {
  position: relative;
  display: grid;
  grid-template-columns: 148px minmax(0, 1fr);
  overflow: hidden;
  min-height: 126px;
  border: 1px solid rgba(39, 212, 255, 0.26);
  border-radius: 10px;
  background: rgba(7, 21, 37, 0.94);
}

.visual-asset-card img {
  width: 100%;
  height: 100%;
  min-height: 126px;
  object-fit: cover;
  object-position: center;
  filter: saturate(1.08) contrast(1.06);
}

.visual-asset-card div {
  display: grid;
  gap: 6px;
  align-content: center;
  border-left: 1px solid rgba(39, 212, 255, 0.18);
  padding: 13px 14px;
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.9), rgba(5, 18, 32, 0.98)),
    #071525;
}

.visual-asset-card span {
  width: fit-content;
  border: 1px solid rgba(39, 212, 255, 0.36);
  border-radius: 999px;
  padding: 4px 8px;
  color: #a9dfff;
  font-size: 12px;
  background: rgba(39, 212, 255, 0.08);
}

.visual-asset-card h2 {
  margin: 0;
  color: #f0f7ff;
  font-size: 17px;
}

.visual-asset-card p {
  margin: 0;
  color: #a9bcd0;
  font-size: 13px;
  line-height: 1.55;
}

.kg-visual-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.kg-visual-card {
  position: relative;
  display: grid;
  grid-template-rows: 190px auto;
  overflow: hidden;
  border: 1px solid rgba(39, 212, 255, 0.32);
  border-radius: 10px;
  padding: 0;
  background: rgba(7, 21, 37, 0.94);
  box-shadow: 0 22px 52px rgba(0, 0, 0, 0.3);
}

.kg-visual-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  filter: saturate(1.08) contrast(1.06);
}

.kg-visual-card__body {
  display: grid;
  gap: 9px;
  border-top: 1px solid rgba(39, 212, 255, 0.22);
  padding: 16px;
  background:
    linear-gradient(180deg, rgba(13, 27, 47, 0.96), rgba(5, 18, 32, 0.98)),
    #071525;
}

.kg-visual-card span {
  display: inline-flex;
  width: fit-content;
  border: 1px solid rgba(39, 212, 255, 0.42);
  border-radius: 999px;
  padding: 5px 9px;
  color: #a9dfff;
  font-size: 12px;
  background: rgba(7, 21, 37, 0.72);
}

.kg-visual-card h2 {
  margin: 0;
  color: #f0f7ff;
  font-size: 20px;
}

.kg-visual-card p {
  max-width: 22em;
  margin: 0;
  color: #b8c9da;
  line-height: 1.55;
}

.kg-visual-card strong {
  width: fit-content;
  border: 1px solid rgba(48, 209, 128, 0.4);
  border-radius: 8px;
  padding: 8px 10px;
  color: #a9ffd1;
  background: rgba(5, 18, 32, 0.76);
}

.kg-management-grid {
  display: grid;
  grid-template-columns: minmax(360px, 1.2fr) minmax(280px, 0.9fr) minmax(320px, 1fr);
  gap: 16px;
}

.kg-management-card,
.kg-governance-card {
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.96), rgba(7, 17, 31, 0.86)),
    linear-gradient(180deg, rgba(7, 17, 31, 0.62), rgba(5, 11, 20, 0.94)),
    url('/steel_kg_evidence_bg.png');
  background-position: center;
  background-size: cover;
}

.kg-asset-list,
.kg-chip-cloud,
.kg-relation-list,
.kg-governance-flow {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 10px;
}

.kg-asset-list span,
.kg-chip-cloud span,
.kg-relation-list span,
.kg-governance-flow span {
  display: grid;
  gap: 5px;
  border: 1px solid rgba(39, 212, 255, 0.22);
  border-radius: 8px;
  padding: 10px;
  background: rgba(5, 18, 32, 0.76);
}

.kg-chip-cloud {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.kg-governance-flow {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kg-asset-list b,
.kg-chip-cloud b,
.kg-relation-list b,
.kg-governance-flow b {
  color: #f0f7ff;
  overflow-wrap: anywhere;
}

.kg-asset-list small,
.kg-chip-cloud small,
.kg-relation-list small,
.kg-governance-flow small,
.kg-asset-list i {
  color: #94acc4;
  font-size: 12px;
  font-style: normal;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.kg-network-card {
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.97), rgba(7, 17, 31, 0.88)),
    radial-gradient(circle at 22% 20%, rgba(39, 212, 255, 0.16), transparent 34%),
    url('/steel_process_knowledge_graph.png');
  background-position: center;
  background-size: cover;
}

.kg-graph-toolbar {
  display: grid;
  grid-template-columns: repeat(4, max-content) minmax(220px, 1fr) minmax(130px, max-content) minmax(150px, max-content) max-content;
  gap: 8px;
  align-items: center;
  margin: 14px 0;
}

.kg-graph-toolbar button {
  white-space: nowrap;
}

.kg-graph-toolbar button.active {
  border-color: #27d4ff;
  color: #eaffff;
  background: rgba(39, 212, 255, 0.14);
  box-shadow: inset 0 0 0 1px rgba(39, 212, 255, 0.2);
}

.kg-graph-toolbar input,
.kg-graph-toolbar select {
  min-width: 0;
}

.kg-graph-toolbar select {
  border: 1px solid #315371;
  border-radius: 8px;
  padding: 9px 10px;
  color: #c7d8e9;
  background: rgba(7, 21, 37, 0.9);
}

.kg-fusion-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin: 0 0 14px;
}

.kg-fusion-strip span {
  display: grid;
  gap: 3px;
  border: 1px solid rgba(39, 212, 255, 0.18);
  border-radius: 8px;
  padding: 10px;
  background: rgba(7, 21, 37, 0.72);
}

.kg-fusion-strip span.warning {
  border-color: rgba(244, 188, 69, 0.52);
  background: rgba(79, 54, 12, 0.36);
}

.kg-fusion-strip b {
  color: #f0f7ff;
  font-size: 18px;
}

.kg-fusion-strip small {
  color: #8ea5bd;
}

.kg-network-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 14px;
  align-items: stretch;
}

.kg-network-canvas,
.kg-network-detail {
  border: 1px solid rgba(39, 212, 255, 0.24);
  border-radius: 8px;
  background: rgba(5, 18, 32, 0.76);
}

.kg-network-canvas {
  position: relative;
  min-height: 560px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 50%, rgba(39, 212, 255, 0.08), transparent 36%),
    linear-gradient(180deg, rgba(5, 13, 24, 0.82), rgba(3, 8, 15, 0.94));
}

.kg-canvas-tools,
.kg-legend {
  position: absolute;
  z-index: 3;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  border: 1px solid rgba(39, 212, 255, 0.18);
  border-radius: 999px;
  padding: 6px;
  background: rgba(4, 12, 22, 0.78);
  backdrop-filter: blur(10px);
}

.kg-canvas-tools {
  top: 12px;
  left: 12px;
}

.kg-canvas-tools button {
  min-width: 32px;
  min-height: 30px;
  border-radius: 999px;
  padding: 5px 10px;
}

.kg-canvas-tools button.active {
  border-color: #27d4ff;
  color: #eaffff;
  background: rgba(39, 212, 255, 0.14);
}

.kg-legend {
  right: 12px;
  bottom: 12px;
}

.kg-legend span {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  color: #9fb6ca;
  font-size: 12px;
}

.kg-legend i {
  width: 9px;
  height: 9px;
  border-radius: 999px;
}

.legend-process {
  background: #27d4ff;
}

.legend-variable {
  background: #7aa7ff;
}

.legend-mechanism {
  background: #ff6f7f;
}

.legend-action {
  background: #30d180;
}

.kg-graph-svg {
  display: block;
  width: 100%;
  height: 560px;
  cursor: move;
  user-select: none;
}

.kg-grid-lines line {
  stroke: rgba(39, 212, 255, 0.045);
  stroke-width: 1;
}

.kg-graph-edges path {
  fill: none;
  stroke: rgba(79, 220, 255, 0.24);
  stroke-linecap: round;
  stroke-width: 1.25;
  transition: stroke 0.16s ease, stroke-width 0.16s ease, opacity 0.16s ease;
}

.kg-graph-edges path.active {
  stroke: #30d180;
  stroke-width: 3;
}

.kg-node {
  cursor: grab;
  outline: none;
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.kg-node:active {
  cursor: grabbing;
}

.kg-node circle {
  fill: #10233d;
  stroke: #4fdcff;
  stroke-width: 2;
  filter: url(#kg-node-glow);
}

.kg-node .kg-node-halo {
  fill: rgba(39, 212, 255, 0.08);
  stroke: transparent;
  filter: none;
}

.kg-node .kg-node-label-bg {
  fill: rgba(4, 12, 22, 0.86);
  stroke: rgba(39, 212, 255, 0.18);
  stroke-width: 1;
  filter: none;
}

.kg-node text {
  fill: #f0f7ff;
  font-size: 11px;
  font-weight: 700;
  text-anchor: middle;
  paint-order: stroke;
  stroke: rgba(5, 11, 20, 0.86);
  stroke-width: 3px;
  stroke-linejoin: round;
}

.kg-node .kg-node-type {
  fill: #a9c5db;
  font-size: 10px;
  font-weight: 500;
}

.kg-node.type-process_step circle:not(.kg-node-halo),
.kg-node.type-equipment_zone circle:not(.kg-node-halo) {
  fill: #0d3651;
  stroke: #27d4ff;
}

.kg-node.type-variable_group circle:not(.kg-node-halo) {
  fill: #17334f;
  stroke: #7aa7ff;
}

.kg-node.type-base_variable circle:not(.kg-node-halo),
.kg-node.type-window_feature circle:not(.kg-node-halo),
.kg-node.type-feature circle:not(.kg-node-halo) {
  fill: #12284b;
  stroke: #8faeff;
}

.kg-node.type-process_state circle:not(.kg-node-halo),
.kg-node.type-defect_mechanism circle:not(.kg-node-halo),
.kg-node.type-quality_class circle:not(.kg-node-halo) {
  fill: #3a2330;
  stroke: #ff6f7f;
}

.kg-node.type-text_evidence circle:not(.kg-node-halo),
.kg-node.type-reviewed_quality_case circle:not(.kg-node-halo) {
  fill: #372d17;
  stroke: #f4bc45;
}

.kg-node.type-correction_action circle:not(.kg-node-halo),
.kg-node.type-action circle:not(.kg-node-halo) {
  fill: #153626;
  stroke: #30d180;
}

.kg-node.selected circle:not(.kg-node-halo) {
  fill: #153626;
  stroke: #a9ffd1;
  stroke-width: 3.5;
}

.kg-node.selected .kg-node-halo,
.kg-node.hovered .kg-node-halo {
  fill: rgba(48, 209, 128, 0.16);
  stroke: rgba(169, 255, 209, 0.28);
  stroke-width: 1.5;
}

.kg-node.hovered circle:not(.kg-node-halo) {
  stroke: #a9ffd1;
  stroke-width: 3;
}

.kg-node.related circle:not(.kg-node-halo) {
  stroke: #f4bc45;
  stroke-width: 2.5;
}

.kg-node.dimmed {
  opacity: 0.38;
}

.kg-network-detail {
  display: grid;
  align-content: start;
  gap: 12px;
  padding: 14px;
}

.kg-network-detail h3 {
  margin: 0;
  color: #f0f7ff;
  font-size: 18px;
}

.kg-network-detail p {
  margin: 0;
  line-height: 1.6;
}

.kg-node-meta,
.kg-selected-relations,
.kg-governance-actions {
  display: grid;
  gap: 8px;
}

.kg-governance-actions {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kg-governance-actions button {
  min-width: 0;
  white-space: normal;
}

.kg-node-meta span,
.kg-selected-relations span {
  display: grid;
  gap: 3px;
  border: 1px solid rgba(39, 212, 255, 0.18);
  border-radius: 8px;
  padding: 9px;
  color: #c7d8e9;
  background: rgba(7, 21, 37, 0.8);
}

.kg-selected-relations b {
  color: #f0f7ff;
}

.kg-selected-relations small {
  color: #94acc4;
}

.kpi span {
  color: #8ea5bd;
}

.kpi strong {
  display: block;
  margin-top: 8px;
  overflow-wrap: anywhere;
  font-size: 22px;
}

.workspace {
  display: grid;
  gap: 16px;
  padding-bottom: 18px;
}

.top-grid,
.analysis-grid,
.two-col,
.summary-grid,
.evidence-grid {
  display: grid;
  gap: 16px;
}

.top-grid {
  grid-template-columns: minmax(0, 1.55fr) minmax(340px, 0.8fr);
}

.analysis-grid {
  grid-template-columns: 320px minmax(0, 1fr) minmax(340px, 0.9fr);
}

.two-col {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-grid,
.evidence-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.inference-chain {
  overflow: hidden;
}

.inference-steps {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
}

.inference-step {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  min-height: 116px;
  border: 1px solid #24405f;
  border-radius: 8px;
  padding: 11px;
  background:
    linear-gradient(180deg, rgba(16, 35, 61, 0.96), rgba(7, 21, 37, 0.96)),
    radial-gradient(circle at 0 0, rgba(39, 212, 255, 0.12), transparent 56%);
}

.inference-step span,
.inference-step small {
  color: #8ea5bd;
}

.inference-step strong {
  margin: 7px 0;
  overflow-wrap: anywhere;
  color: #e7f0fb;
}

.inference-step i {
  display: block;
  height: 5px;
  border-radius: 999px;
  background: linear-gradient(90deg, #27d4ff, #30d180);
}

.model-flow-card,
.model-gate-card {
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.96), rgba(7, 17, 31, 0.88)),
    linear-gradient(180deg, rgba(7, 17, 31, 0.62), rgba(5, 11, 20, 0.94)),
    url('/steel_evidence_fusion_graph.png');
  background-position: center;
  background-size: cover;
}

.model-flow-card > *,
.model-gate-card > * {
  position: relative;
  z-index: 1;
}

.model-flow-grid,
.model-metric-row,
.gate-grid {
  display: grid;
  gap: 12px;
}

.model-flow-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 12px;
}

.model-stage-card,
.model-metric,
.gate-policy,
.model-feature-list,
.cascade-evidence-list button {
  display: grid;
  gap: 7px;
  border: 1px solid rgba(39, 212, 255, 0.24);
  border-radius: 8px;
  padding: 12px;
  color: #c7d8e9;
  background: rgba(7, 21, 37, 0.88);
}

.model-stage-card span,
.model-metric span,
.model-feature-list b,
.gate-policy b {
  color: #a9dfff;
  font-weight: 700;
}

.model-stage-card strong {
  color: #f0f7ff;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.model-metric-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 12px;
}

.model-metric strong {
  color: #fff;
  font-size: 26px;
}

.model-metric .metric-raw {
  color: rgba(169, 223, 255, 0.68);
  font-size: 12px;
}

.model-metric i {
  display: block;
  height: 5px;
  border-radius: 999px;
  background: linear-gradient(90deg, #2f7dff, #27d4ff, #30d180);
}

.gate-grid {
  grid-template-columns: minmax(340px, 0.8fr) minmax(0, 1.2fr);
}

.model-dataset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.model-dataset-row span {
  border: 1px solid rgba(48, 209, 128, 0.35);
  border-radius: 999px;
  padding: 5px 9px;
  color: #a9ffd1;
  background: rgba(48, 209, 128, 0.08);
}

.model-feature-list span {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border-bottom: 1px solid rgba(36, 64, 95, 0.74);
  padding-bottom: 7px;
}

.model-feature-list span:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.model-feature-list i {
  color: #30d180;
  font-style: normal;
}

.cascade-evidence-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.cascade-evidence-list button {
  text-align: left;
}

.cascade-evidence-list b {
  color: #fff;
}

.cascade-evidence-list span,
.cascade-evidence-list small {
  color: #9db2c6;
  line-height: 1.5;
}

.span-2 {
  grid-column: span 2;
}

.knowledge-hub-card {
  border-color: rgba(39, 212, 255, 0.34);
  background:
    linear-gradient(90deg, rgba(39, 212, 255, 0.11), transparent 48%),
    rgba(7, 21, 37, 0.94);
}

.knowledge-hub-grid,
.candidate-review-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.knowledge-hub-grid span,
.candidate-review-grid span {
  display: grid;
  gap: 6px;
  border: 1px solid rgba(39, 212, 255, 0.22);
  border-radius: 8px;
  padding: 12px;
  background: rgba(8, 25, 43, 0.82);
}

.knowledge-hub-grid b,
.candidate-review-grid b {
  color: #f0f7ff;
}

.knowledge-hub-grid small,
.candidate-review-grid small,
.candidate-review-grid i {
  color: #a9bfd3;
  font-style: normal;
  line-height: 1.5;
}

.candidate-review-card {
  border-color: rgba(48, 209, 128, 0.26);
}

.candidate-review-grid {
  margin: 12px 0;
}

.candidate-review-grid b {
  color: #30d180;
  font-size: 26px;
}

.candidate-validation-list {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(39, 212, 255, 0.22);
  border-radius: 8px;
  padding: 12px;
  background: rgba(7, 21, 37, 0.82);
}

.candidate-validation-list span {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid rgba(36, 64, 95, 0.72);
  padding-top: 8px;
  color: #c7d8e9;
}

.candidate-validation-list small {
  flex-shrink: 0;
  color: #30d180;
}

.panel h2,
.panel h3 {
  margin: 0 0 12px;
}

.panel h2 {
  font-size: 18px;
}

.panel h3 {
  margin-top: 16px;
  font-size: 14px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.risk-ring {
  display: grid;
  width: 148px;
  aspect-ratio: 1;
  margin: 4px auto 14px;
  place-items: center;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, #0d1b2f 0 58%, transparent 59%),
    conic-gradient(#27d4ff calc(var(--p) * 1%), #203852 0);
}

.prob-row {
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  margin-bottom: 10px;
}

.prob-row i {
  grid-column: 1 / -1;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, #27d4ff, #30d180);
}

.path-library span,
.basis-result-card {
  display: grid;
  gap: 5px;
  border: 1px solid #24405f;
  border-radius: 8px;
  margin-bottom: 10px;
  padding: 11px;
  background: #071525;
}

.metric-list,
.path-library,
.basis-results {
  display: grid;
  gap: 8px;
}

.basis-result-card {
  position: relative;
  overflow: hidden;
  gap: 10px;
}

.basis-result-card::before {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  content: '';
  background: linear-gradient(180deg, #27d4ff, #30d180);
}

.basis-result-head {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.basis-result-head span {
  border: 1px solid rgba(39, 212, 255, 0.35);
  border-radius: 999px;
  padding: 4px 8px;
  color: #a9dfff;
  font-size: 12px;
  background: rgba(39, 212, 255, 0.1);
}

.basis-result-head b {
  min-width: 0;
  color: #f0f7ff;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.basis-result-card p,
.basis-result-card i {
  margin: 0;
  color: #b8c9da;
  line-height: 1.6;
}

.basis-result-card i {
  display: block;
  border-top: 1px solid rgba(36, 64, 95, 0.72);
  padding-top: 8px;
  color: #8ea5bd;
  font-style: normal;
}

.basis-result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.basis-result-meta small {
  border: 1px solid rgba(142, 165, 189, 0.22);
  border-radius: 999px;
  padding: 4px 7px;
  color: #9bb4cc;
  background: rgba(5, 18, 32, 0.72);
}

.basis-empty {
  border: 1px dashed rgba(142, 165, 189, 0.28);
  border-radius: 8px;
  padding: 14px;
  color: #8ea5bd;
  background: rgba(5, 18, 32, 0.52);
}

.metric-list span {
  border: 1px solid #24405f;
  border-radius: 8px;
  padding: 8px;
  color: #c7d8e9;
  background: #071525;
}

table {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 8px;
}

th,
td {
  border-bottom: 1px solid #24405f;
  padding: 10px;
  color: #c7d8e9;
  text-align: left;
}

tbody tr {
  cursor: pointer;
}

tbody tr:hover {
  background: rgba(39, 212, 255, 0.08);
}

input,
textarea {
  width: 100%;
  border: 1px solid #2f5578;
  border-radius: 8px;
  padding: 10px;
  color: #e7f0fb;
  background: #071525;
}

textarea {
  min-height: 148px;
  resize: vertical;
}

.qa-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
}

.answer {
  margin-top: 12px;
  border: 1px solid #24405f;
  border-radius: 8px;
  padding: 12px;
  color: #c7d8e9;
  line-height: 1.7;
  background: #071525;
}

.assistant-status {
  border: 1px solid rgba(39, 212, 255, 0.24);
  border-radius: 999px;
  padding: 7px 10px;
  color: #a9dfff;
  font-size: 12px;
  background: rgba(39, 212, 255, 0.08);
}

.case-ingest-status {
  margin-top: 10px;
  border: 1px solid rgba(244, 188, 69, 0.34);
  border-radius: 8px;
  padding: 9px 10px;
  color: #ffd98a;
  background: rgba(244, 188, 69, 0.08);
}

.candidate-list {
  display: grid;
  gap: 7px;
  margin-top: 12px;
  border: 1px solid rgba(39, 212, 255, 0.25);
  border-radius: 8px;
  padding: 10px;
  color: #c7d8e9;
  background: #071525;
}

.candidate-list span {
  color: #8ea5bd;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.feedback-btn {
  margin-top: 12px;
}

.operation-log {
  padding-bottom: 18px;
}

.operation-log span {
  border: 1px solid rgba(48, 209, 128, 0.28);
  border-radius: 999px;
  padding: 6px 10px;
  color: #a9ffd1;
  background: rgba(48, 209, 128, 0.08);
}

.assistant-toggle {
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 20;
  border-color: rgba(39, 212, 255, 0.7);
  color: #03101b;
  font-weight: 700;
  background: linear-gradient(135deg, #2f7dff, #27d4ff);
  box-shadow: 0 12px 34px rgba(39, 212, 255, 0.22);
}

.assistant-drawer {
  position: fixed;
  top: 92px;
  right: 22px;
  z-index: 21;
  display: grid;
  gap: 12px;
  width: min(420px, calc(100vw - 44px));
  max-height: calc(100vh - 128px);
  overflow: auto;
  border: 1px solid rgba(39, 212, 255, 0.34);
  border-radius: 10px;
  padding: 16px;
  color: #e7f0fb;
  background: rgba(7, 17, 31, 0.96);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(12px);
}

.assistant-evidence {
  display: grid;
  gap: 8px;
  border: 1px solid #24405f;
  border-radius: 8px;
  padding: 10px;
  background: #071525;
}

.assistant-evidence span {
  color: #8ea5bd;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1280px) {
  .steel-shell,
  .top-grid,
  .analysis-grid,
  .two-col,
  .summary-grid,
  .evidence-grid,
  .inference-steps,
  .visual-frame-card,
  .visual-asset-grid,
  .kg-visual-grid,
  .kg-management-grid,
  .kg-network-layout,
  .kg-governance-flow,
  .model-flow-grid,
  .model-metric-row,
  .knowledge-hub-grid,
  .candidate-review-grid,
  .gate-grid,
  .cascade-evidence-list {
    grid-template-columns: 1fr;
  }

  .module-tabs {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .module-tabs::-webkit-scrollbar {
    display: none;
  }

  .module-tabs button {
    min-width: 160px;
  }

  .visual-frame-card__image {
    height: 260px;
  }

  .kg-graph-toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .visual-asset-card {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .kg-visual-card {
    grid-template-rows: 220px auto;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .span-2 {
    grid-column: auto;
  }
  .topbar {
    align-items: flex-start;
    flex-direction: column;
    padding: 16px 18px;
  }
}

@media (max-width: 720px) {
  .module-tabs button {
    grid-template-columns: 56px minmax(0, 1fr);
    min-width: 210px;
  }

  .module-tab__thumb {
    width: 52px;
    height: 52px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .visual-frame-card__image {
    height: 210px;
  }

  .visual-asset-card {
    grid-template-columns: 1fr;
  }

  .visual-asset-card img {
    height: 170px;
  }

  .visual-asset-card div {
    border-top: 1px solid rgba(39, 212, 255, 0.18);
    border-left: 0;
  }

  .kg-visual-card {
    grid-template-rows: 180px auto;
  }
}
</style>
