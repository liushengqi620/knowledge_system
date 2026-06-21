<template>
  <section class="trace-review" aria-label="原因链路与证据复核">
    <div class="trace-review__head">
      <div>
        <span class="eyebrow">现场原因复核</span>
        <h2>原因链路与证据复核</h2>
        <p>把实时信号、工艺位置、异常机理、历史案例和处置建议组织成班组可复核的原因链路。</p>
      </div>
      <div class="trace-review__status">
        <b>{{ paths.length }}</b>
        <span>条候选原因</span>
      </div>
    </div>

    <div v-if="!paths.length" class="trace-empty">
      <b>当前事件暂无候选原因链路</b>
      <span>当异常预警触发且模型返回候选路径后，这里会显示原因链路、证据来源和复核建议。</span>
    </div>

    <div v-else class="trace-review__layout">
      <aside class="cause-list" aria-label="候选原因列表">
        <button
          v-for="(path, index) in paths"
          :key="`${path.feature}-${path.defect_mechanism}-${index}`"
          :class="['cause-card', { active: index === selectedIndex }]"
          type="button"
          @click="selectPath(index)"
        >
          <span class="cause-card__rank">原因 {{ index + 1 }}</span>
          <strong>{{ labelName(path.equipment_zone) }}：{{ labelName(path.defect_mechanism) }}</strong>
          <small>{{ labelName(path.feature) }} / {{ labelName(path.variable_group) }}</small>
          <div class="confidence-line">
            <i :style="{ width: `${scorePercent(path.final_score || path.path_score)}%` }" />
          </div>
          <div class="cause-card__meta">
            <span>{{ scoreLevel(path.final_score || path.path_score) }}</span>
            <span>图谱命中 {{ path.graph_evidence_detail?.matched_relation_count || 0 }}</span>
            <span>{{ pathLibraryText(path) }}</span>
          </div>
        </button>
      </aside>

      <main class="trace-workbench">
        <div class="trace-workbench__summary">
          <div>
            <span class="eyebrow">当前复核链路</span>
            <h3>{{ selectedPathTitle }}</h3>
            <p>{{ selectedPathSummary }}</p>
          </div>
          <div :class="['decision-badge', decisionTone]">
            <b>{{ qualityDecision.title }}</b>
            <span>{{ qualityDecision.note }}</span>
          </div>
        </div>

        <div class="path-flow" aria-label="原因链路节点">
          <button
            v-for="(node, index) in selectedPath?.nodes || []"
            :key="`${node.layer}-${node.id}-${index}`"
            :class="['path-step', nodeClass(node.layer), { active: index === selectedNodeIndex }]"
            type="button"
            @click="selectedNodeIndex = index"
          >
            <span>{{ index + 1 }}</span>
            <strong>{{ labelName(node.label) }}</strong>
            <small>{{ layerText(node.layer) }}</small>
          </button>
        </div>

        <div class="evidence-overview">
          <article v-for="item in evidenceOverview" :key="item.key">
            <span>{{ item.title }}</span>
            <b>{{ item.value }}</b>
            <small>{{ item.note }}</small>
          </article>
        </div>

        <div class="selected-node-panel" v-if="selectedNode">
          <span>当前查看节点</span>
          <b>{{ labelName(selectedNode.label) }}</b>
          <small>{{ layerText(selectedNode.layer) }}</small>
        </div>
      </main>

      <aside class="review-panel" aria-label="链路证据详情">
        <div class="review-block">
          <span class="eyebrow">复核结论</span>
          <h3>{{ qualityDecision.title }}</h3>
          <p>{{ qualityDecision.detail }}</p>
        </div>

        <dl class="detail-grid">
          <dt>关键参数</dt>
          <dd>{{ labelName(selectedPath?.feature) }}</dd>
          <dt>当前值</dt>
          <dd>{{ featureValueText(selectedPath?.feature_value) }}</dd>
          <dt>信号类别</dt>
          <dd>{{ labelName(selectedPath?.variable_group) }}</dd>
          <dt>工艺位置</dt>
          <dd>{{ labelName(selectedPath?.equipment_zone) }}</dd>
          <dt>综合可信度</dt>
          <dd>{{ fmt(selectedPath?.final_score || selectedPath?.path_score) }}</dd>
          <dt>评分方式</dt>
          <dd>{{ scoreModelName(selectedPath?.score_model) }}</dd>
        </dl>

        <div class="score-stack">
          <b>复核指标拆解</b>
          <span v-for="item in scoreBreakdown" :key="item.key">
            <i :style="{ width: `${scorePercent(item.value)}%` }" />
            <em>{{ item.label }}</em>
            <strong>{{ fmt(item.value) }}</strong>
            <small>{{ item.note }}</small>
          </span>
        </div>

        <div class="graph-hit-stack" v-if="matchedRelations.length">
          <b>图谱命中依据</b>
          <span v-for="(relation, index) in matchedRelations.slice(0, 8)" :key="`${relation.relation_type}-${index}`">
            <em>{{ relationLabel(relation) }}</em>
            <small>{{ relationTypeText(String(relation.relation_type || '')) }} / 置信度 {{ fmt(Number(relation.confidence || 0)) }}</small>
          </span>
        </div>

        <div class="evidence-groups">
          <b>证据来源</b>
          <article v-for="group in evidenceGroups" :key="group.key">
            <span>{{ group.title }}</span>
            <strong>{{ group.items.length }} 条</strong>
            <small>{{ group.note }}</small>
            <p v-for="source in group.items.slice(0, 2)" :key="source.source_id">
              {{ evidenceTitle(source.title) }} / 置信度 {{ fmt(source.confidence) }}
            </p>
          </article>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { EvidenceSource, TraceNode, TracePath } from '../types/steelRealtime';
import {
  formatSourceType,
  formatSteelTerm,
  tracePathSummary,
  tracePathTitle,
} from '../utils/steelTerminology';

const props = defineProps<{
  paths: TracePath[];
  labels: Record<string, string>;
}>();

const selectedIndex = ref(0);
const selectedNodeIndex = ref(0);

const selectedPath = computed(() => props.paths[selectedIndex.value]);
const selectedNode = computed<TraceNode | undefined>(() => selectedPath.value?.nodes?.[selectedNodeIndex.value]);
const matchedRelations = computed(() => {
  return (selectedPath.value?.graph_evidence_detail?.matched_relations || []) as Array<{
    label?: string;
    relation_type?: string;
    confidence?: number;
  }>;
});

const selectedPathTitle = computed(() => {
  const path = selectedPath.value;
  return path ? pathTitle(path, selectedIndex.value) : '等待候选原因';
});

const selectedPathSummary = computed(() => {
  const path = selectedPath.value;
  return path ? pathSummary(path) : '当前事件暂无可复核链路';
});

const qualityDecision = computed(() => {
  const score = Number(selectedPath.value?.final_score || selectedPath.value?.path_score || 0);
  const hits = Number(selectedPath.value?.graph_evidence_detail?.matched_relation_count || 0);
  if (score >= 0.75 && hits >= 4) {
    return {
      tone: 'high',
      title: '高可信原因',
      note: '建议优先现场复核',
      detail: '模型输出、图谱关系和历史链路支持度较高，可作为当前事件的优先排查方向。',
    };
  }
  if (score >= 0.6) {
    return {
      tone: 'medium',
      title: '较可信原因',
      note: '建议结合现场确认',
      detail: '该链路已有一定证据支持，但仍需要结合现场状态、设备记录和班组处置反馈确认。',
    };
  }
  return {
    tone: 'low',
    title: '待补充证据',
    note: '建议保留观察',
    detail: '当前链路证据不足，建议继续观察实时趋势，补充文本规程、历史案例或人工复核记录。',
  };
});

const decisionTone = computed(() => `tone-${qualityDecision.value.tone}`);

const evidenceOverview = computed(() => {
  const path = selectedPath.value;
  return [
    {
      key: 'signal',
      title: '现场信号',
      value: fmt(path?.model_attribution || path?.path_score),
      note: `${labelName(path?.feature)} / ${featureValueText(path?.feature_value)}`,
    },
    {
      key: 'graph',
      title: '图谱证据',
      value: `${path?.graph_evidence_detail?.matched_relation_count || 0} 条命中`,
      note: `图谱先验 ${fmt(path?.graph_prior)}`,
    },
    {
      key: 'history',
      title: '历史链路',
      value: pathLibraryText(path),
      note: `历史评分 ${fmt(path?.path_library_score)}`,
    },
    {
      key: 'time',
      title: '时序一致性',
      value: fmt(path?.temporal_consistency),
      note: '结合风险阶段与提前量',
    },
  ];
});

const scoreBreakdown = computed(() => {
  const path = selectedPath.value;
  return [
    {
      key: 'model',
      label: '现场信号贡献',
      value: path?.model_attribution || path?.path_score,
      note: '由实时生产参数和模型归因形成',
    },
    {
      key: 'graph',
      label: '图谱证据强度',
      value: path?.graph_prior,
      note: '由命中关系、历史链路和来源多样性形成',
    },
    {
      key: 'temporal',
      label: '时序一致性',
      value: path?.temporal_consistency,
      note: '检查异常发展阶段是否合理',
    },
    {
      key: 'rule',
      label: '专家规则对齐',
      value: path?.expert_rule_alignment,
      note: '检查是否符合工艺经验与处置规则',
    },
    {
      key: 'process',
      label: '工艺一致性',
      value: path?.process_consistency,
      note: '检查变量组、工艺位置和机理是否匹配',
    },
  ];
});

const evidenceGroups = computed(() => {
  const sources = selectedPath.value?.evidence_sources || [];
  const config = [
    {
      key: 'structured_production',
      title: '结构化生产信号',
      note: '来自实时生产记录、事件窗口和关键工艺变量',
    },
    {
      key: 'knowledge_graph',
      title: '知识图谱证据',
      note: '来自变量、工序、机理、质量类别之间的已发布关系',
    },
    {
      key: 'text_knowledge',
      title: '文本知识依据',
      note: '来自规程、异常报告、专家经验或知识抽取结果',
    },
    {
      key: 'expert_rule',
      title: '专家规则与处置',
      note: '来自工艺规则、处置建议和人工复核闭环',
    },
  ];
  return config.map((group) => ({
    ...group,
    items: sources.filter((source) => source.source_type === group.key),
  }));
});

watch(
  () => props.paths,
  () => {
    selectedIndex.value = 0;
    selectedNodeIndex.value = 0;
  },
);

function selectPath(index: number) {
  selectedIndex.value = index;
  selectedNodeIndex.value = 0;
}

function fmt(value?: number | string | null) {
  if (typeof value === 'number') return value.toFixed(3);
  if (typeof value === 'string' && value.trim()) return value;
  return '-';
}

function scorePercent(value?: number | string | null) {
  const number = Number(value || 0);
  return Math.max(0, Math.min(100, Math.round(number * 100)));
}

function scoreLevel(value?: number | string | null) {
  const number = Number(value || 0);
  if (number >= 0.8) return '高可信';
  if (number >= 0.65) return '较可信';
  if (number > 0) return '需复核';
  return '待评估';
}

function featureValueText(value?: number | string | null) {
  return typeof value === 'number' ? value.toFixed(3) : value || '-';
}

function labelName(value?: string) {
  return formatSteelTerm(value, props.labels);
}

function pathTitle(path: TracePath, index: number) {
  return tracePathTitle(path, index, props.labels);
}

function pathSummary(path: TracePath) {
  return tracePathSummary(path, props.labels);
}

function layerText(layer?: string) {
  const map: Record<string, string> = {
    window_feature: '实时窗口参数',
    variable_group: '信号类别',
    equipment_zone: '工艺位置',
    process_state: '工艺状态',
    defect_mechanism: '异常机理',
    event_quality_class: '异常种类',
    correction_action: '处置建议',
  };
  return (layer && map[layer]) || layer || '-';
}

function nodeClass(layer?: string) {
  const map: Record<string, string> = {
    window_feature: 'node-signal',
    variable_group: 'node-signal',
    equipment_zone: 'node-process',
    process_state: 'node-state',
    defect_mechanism: 'node-risk',
    event_quality_class: 'node-risk',
    correction_action: 'node-action',
  };
  return (layer && map[layer]) || 'node-default';
}

function sourceTypeName(sourceType?: string) {
  return formatSourceType(sourceType);
}

function evidenceTitle(value?: string) {
  if (!value) return '-';
  let text = value;
  for (const key of Object.keys(props.labels || {}).sort((a, b) => b.length - a.length)) {
    text = text.split(key).join(labelName(key));
  }
  return text;
}

function scoreModelName(value?: string) {
  const map: Record<string, string> = {
    kg_evidence_fusion_v2: '知识图谱证据融合评分',
  };
  return (value && map[value]) || value || '候选路径评分';
}

function pathLibraryText(path?: TracePath) {
  if (!path) return '-';
  if (!path.path_library_match) return '未命中历史';
  return `${path.path_library_event_count || 0} 次历史命中`;
}

function relationLabel(relation: { label?: string }) {
  return labelName(relation.label || '图谱关系');
}

function relationTypeText(value?: string) {
  const map: Record<string, string> = {
    HAS_STAT_FEATURE: '基础变量形成窗口指标',
    BELONGS_TO_VARIABLE_GROUP: '窗口指标归属信号类别',
    HAS_KEY_SIGNAL: '案例包含关键信号',
    OBSERVED_IN_ZONE: '信号关联工艺位置',
    INDICATES_MECHANISM: '工艺位置指向异常机理',
    HAS_RISK_MECHANISM: '工序关联风险机理',
    SUPPORTS_MECHANISM: '信号支持异常机理',
    SUPPORTS_PROCESS_STATE: '信号支持工艺状态',
    STATE_INDICATES_MECHANISM: '工艺状态指向异常机理',
    CAUSES_QUALITY_RISK: '机理对应质量异常',
    SUPPORTED_BY_TEXT: '文本知识支持机理',
    SUPPORTED_BY_CASE: '历史案例支持机理',
    SUGGESTS_ACTION: '机理绑定处置建议',
  };
  return (value && map[value]) || value || '-';
}
</script>

<style scoped>
.trace-review {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(36, 64, 95, 0.9);
  border-radius: 10px;
  padding: 18px;
  color: #e7f0fb;
  background:
    linear-gradient(90deg, rgba(13, 27, 47, 0.97), rgba(7, 17, 31, 0.86)),
    radial-gradient(circle at 62% 44%, rgba(39, 212, 255, 0.13), transparent 32%),
    url('/steel_trace_path_bg.png');
  background-position: center;
  background-size: cover;
}

.trace-review::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: '';
  background:
    linear-gradient(90deg, rgba(39, 212, 255, 0.07), transparent 28%, transparent 72%, rgba(48, 209, 128, 0.08)),
    radial-gradient(circle at 86% 12%, rgba(255, 92, 101, 0.12), transparent 22%);
}

.trace-review > * {
  position: relative;
  z-index: 1;
}

.trace-review__head,
.trace-review__layout,
.trace-workbench__summary,
.evidence-overview,
.cause-card__meta {
  display: grid;
  gap: 12px;
}

.trace-review__head {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.eyebrow {
  color: #7fdcff;
  font-size: 12px;
}

.trace-review h2,
.trace-review h3,
.trace-review p {
  margin: 0;
}

.trace-review h2 {
  margin-top: 4px;
  font-size: 24px;
}

.trace-review__head p,
.trace-workbench__summary p,
.review-block p,
.selected-node-panel small,
.evidence-overview small,
.score-stack small,
.evidence-groups small,
.evidence-groups p {
  color: #8ea5bd;
  line-height: 1.55;
}

.trace-review__status,
.decision-badge {
  border: 1px solid rgba(39, 212, 255, 0.25);
  border-radius: 12px;
  padding: 10px 14px;
  background: rgba(7, 21, 37, 0.72);
}

.trace-review__status b {
  display: block;
  color: #a9ffd1;
  font-size: 24px;
}

.trace-review__status span {
  color: #8ea5bd;
}

.trace-empty {
  display: grid;
  gap: 6px;
  margin-top: 16px;
  border: 1px dashed rgba(39, 212, 255, 0.32);
  border-radius: 10px;
  padding: 18px;
  color: #c7d8e9;
  background: rgba(7, 21, 37, 0.68);
}

.trace-review__layout {
  grid-template-columns: 300px minmax(520px, 1fr) 340px;
  margin-top: 16px;
}

.cause-list,
.review-panel,
.trace-workbench,
.score-stack,
.evidence-groups,
.graph-hit-stack {
  display: grid;
  gap: 10px;
}

.cause-list {
  align-content: start;
}

.cause-card {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(36, 64, 95, 0.95);
  border-radius: 10px;
  padding: 12px;
  color: #d8e6f5;
  text-align: left;
  background: rgba(7, 21, 37, 0.88);
  cursor: pointer;
}

.cause-card.active,
.cause-card:hover {
  border-color: #27d4ff;
  background: rgba(39, 212, 255, 0.1);
  box-shadow: inset 3px 0 0 #27d4ff;
}

.cause-card__rank {
  color: #7fdcff;
  font-size: 12px;
}

.cause-card strong {
  line-height: 1.35;
}

.cause-card small,
.cause-card__meta span {
  color: #8ea5bd;
  line-height: 1.45;
}

.confidence-line {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(49, 83, 113, 0.58);
}

.confidence-line i,
.score-stack i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #27d4ff, #30d180);
}

.cause-card__meta {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  font-size: 12px;
}

.trace-workbench {
  min-width: 0;
  border: 1px solid rgba(36, 64, 95, 0.95);
  border-radius: 10px;
  padding: 14px;
  background:
    linear-gradient(90deg, rgba(7, 21, 37, 0.9), rgba(7, 21, 37, 0.62) 50%, rgba(7, 21, 37, 0.9)),
    linear-gradient(rgba(39, 212, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(39, 212, 255, 0.08) 1px, transparent 1px),
    url('/steel_abnormal_propagation_graph.png');
  background-position: center, 0 0, 0 0, center;
  background-size: cover, 38px 38px, 38px 38px, cover;
  box-shadow: inset 0 0 48px rgba(0, 0, 0, 0.32);
}

.trace-workbench__summary {
  grid-template-columns: minmax(0, 1fr) 190px;
  align-items: stretch;
}

.decision-badge {
  display: grid;
  align-content: center;
  gap: 4px;
}

.decision-badge b {
  font-size: 18px;
}

.decision-badge span {
  color: #c7d8e9;
  font-size: 12px;
}

.tone-high {
  border-color: rgba(48, 209, 128, 0.52);
  background: rgba(13, 54, 38, 0.7);
}

.tone-medium {
  border-color: rgba(244, 188, 69, 0.52);
  background: rgba(70, 48, 15, 0.58);
}

.tone-low {
  border-color: rgba(255, 111, 127, 0.52);
  background: rgba(66, 31, 39, 0.56);
}

.path-flow {
  display: flex;
  gap: 12px;
  align-items: stretch;
  min-height: 136px;
  overflow-x: auto;
  padding: 12px 4px 18px;
}

.path-step {
  position: relative;
  display: grid;
  grid-template-rows: auto minmax(42px, auto) auto;
  gap: 7px;
  align-content: center;
  min-width: 150px;
  border: 1px solid rgba(47, 85, 120, 0.95);
  border-radius: 10px;
  padding: 12px;
  color: #e7f0fb;
  background: rgba(11, 27, 48, 0.92);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
  cursor: pointer;
}

.path-step:not(:last-child)::after {
  position: absolute;
  top: 50%;
  right: -13px;
  z-index: 2;
  width: 13px;
  height: 2px;
  content: '';
  background: #27d4ff;
  box-shadow: 0 0 14px rgba(39, 212, 255, 0.7);
}

.path-step.active {
  border-color: #a9ffd1;
  box-shadow: 0 0 0 1px rgba(169, 255, 209, 0.25), 0 14px 28px rgba(0, 0, 0, 0.28);
}

.path-step span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  color: #071525;
  font-weight: 800;
  background: #27d4ff;
}

.path-step strong {
  line-height: 1.28;
}

.path-step small {
  color: #8ea5bd;
}

.node-signal {
  border-color: rgba(122, 167, 255, 0.72);
}

.node-process,
.node-state {
  border-color: rgba(39, 212, 255, 0.72);
}

.node-risk {
  border-color: rgba(255, 111, 127, 0.75);
}

.node-action {
  border-color: rgba(48, 209, 128, 0.75);
}

.evidence-overview {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.evidence-overview article,
.selected-node-panel,
.review-block,
.detail-grid,
.score-stack,
.graph-hit-stack,
.evidence-groups article {
  border: 1px solid rgba(39, 212, 255, 0.2);
  border-radius: 10px;
  padding: 10px;
  background: rgba(5, 18, 32, 0.74);
}

.evidence-overview span,
.selected-node-panel span,
.review-block .eyebrow {
  color: #7fdcff;
  font-size: 12px;
}

.evidence-overview b,
.selected-node-panel b {
  display: block;
  margin: 5px 0;
  color: #f0f7ff;
  font-size: 18px;
}

.selected-node-panel {
  display: grid;
  gap: 4px;
}

.review-panel {
  align-content: start;
}

.review-block h3 {
  margin-top: 5px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 90px minmax(0, 1fr);
  gap: 8px;
}

.detail-grid dt {
  color: #8ea5bd;
}

.detail-grid dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
}

.score-stack span {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 54px;
  gap: 4px 8px;
  align-items: center;
}

.score-stack i {
  grid-column: 1 / -1;
  height: 6px;
  background: linear-gradient(90deg, #27d4ff, #f4bc45);
}

.score-stack em,
.graph-hit-stack em {
  color: #d8e6f5;
  font-style: normal;
}

.score-stack strong {
  text-align: right;
}

.score-stack small {
  grid-column: 1 / -1;
}

.graph-hit-stack span,
.evidence-groups article {
  display: grid;
  gap: 4px;
}

.graph-hit-stack {
  border-color: rgba(48, 209, 128, 0.28);
  background: rgba(48, 209, 128, 0.06);
}

.evidence-groups b,
.score-stack b,
.graph-hit-stack b {
  color: #f0f7ff;
}

.evidence-groups article strong {
  color: #a9ffd1;
}

.evidence-groups p {
  margin: 0;
  font-size: 12px;
}

@media (max-width: 1380px) {
  .trace-review__layout {
    grid-template-columns: 280px minmax(460px, 1fr);
  }

  .review-panel {
    grid-column: 1 / -1;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .trace-review__head,
  .trace-review__layout,
  .trace-workbench__summary,
  .evidence-overview,
  .review-panel {
    grid-template-columns: 1fr;
  }
}
</style>
