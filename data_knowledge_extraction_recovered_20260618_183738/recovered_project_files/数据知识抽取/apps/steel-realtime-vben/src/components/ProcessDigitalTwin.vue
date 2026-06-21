<template>
  <section class="process-card" aria-label="钢铁全流程动态示意">
    <div class="process-card__head">
      <div>
        <h2>实时监测溯源总览</h2>
        <p>当前区域由事件窗口、风险预警、异常识别、原因链路和处置建议实时驱动</p>
      </div>
      <span class="scope-badge" aria-label="当前重点：连铸段">当前重点：{{ focusName }}</span>
    </div>

    <div class="live-summary">
      <div class="event-chip">
        <span :class="['pulse-dot', `is-${riskLevel}`]" />
        <div>
          <b>{{ eventName }}</b>
          <small>{{ riskLevelName }} / 风险值 {{ riskScore }}</small>
        </div>
      </div>
      <div class="summary-metrics">
        <span>工序状态 {{ steps.length }} 项</span>
        <span>候选原因 {{ tracePathCount }} 条</span>
        <span>复核依据 {{ evidenceCount }} 条</span>
      </div>
    </div>

    <div class="monitor-chain">
      <article
        v-for="(stage, index) in monitorStages"
        :key="stage.key"
        :class="['chain-stage', `is-${stage.state}`]"
      >
        <span class="stage-index">{{ String(index + 1).padStart(2, '0') }}</span>
        <b>{{ stage.title }}</b>
        <strong>{{ stage.value }}</strong>
        <small>{{ stage.note }}</small>
      </article>
    </div>

    <div class="process-rail">
      <button
        v-for="step in steps"
        :key="step.id"
        class="process-node"
        :class="[`is-${step.status}`, { 'is-context': step.scope === 'context' }]"
        type="button"
        @click="$emit('select-step', step.id)"
      >
        <span class="node-name">{{ step.name }}</span>
        <span class="node-note">{{ step.note }}</span>
        <span class="node-status">{{ statusName(step.status) }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ProcessStepStatus, SteelRealtimeEvent } from '../types/steelRealtime';
import {
  eventDisplayTitle,
  formatSteelTerm,
  riskLevelName as formatRiskLevelName,
} from '../utils/steelTerminology';

const props = defineProps<{
  steps: ProcessStepStatus[];
  activeEvent?: SteelRealtimeEvent;
  labels?: Record<string, string>;
}>();

defineEmits<{
  (event: 'select-step', stepId: string): void;
}>();

const topPath = computed(() => props.activeEvent?.traceability?.top_k_paths?.[0]);
const riskLevel = computed(() => props.activeEvent?.risk_warning?.risk_level || 'low');
const riskScore = computed(() => {
  const value = props.activeEvent?.risk_warning?.risk_probability;
  return typeof value === 'number' ? value.toFixed(3) : '-';
});
const riskLevelName = computed(() => {
  return formatRiskLevelName(riskLevel.value);
});
const tracePathCount = computed(() => props.activeEvent?.traceability?.top_k_paths?.length || 0);
const evidenceCount = computed(() => topPath.value?.evidence_sources?.length || 0);
const focusName = computed(() => {
  const focused = props.steps.find((step) => ['danger', 'warning', 'active'].includes(step.status));
  return focused?.name || labelName(topPath.value?.equipment_zone) || '连铸段';
});
const eventName = computed(() => {
  return eventDisplayTitle(props.activeEvent, props.labels);
});
const primaryClass = computed(() => {
  const ident = props.activeEvent?.abnormal_identification;
  const key = ident?.display_groups?.[0]
    || ident?.primary_abnormal_class
    || ident?.predicted_abnormal_groups?.[0]
    || '';
  return labelName(key) || '待识别事件';
});
const actionText = computed(() => props.activeEvent?.recommendation?.recommended_checks?.[0] || '待班组复核');

const monitorStages = computed(() => [
  {
    key: 'signal',
    title: '生产信号',
    value: `${props.steps.length || 0} 个工序`,
    note: '结构化事件窗口输入',
    state: 'normal',
  },
  {
    key: 'risk',
    title: '质量预警',
    value: riskLevelName.value,
    note: `风险值 ${riskScore.value}`,
    state: riskLevel.value,
  },
  {
    key: 'identify',
    title: '异常识别',
    value: primaryClass.value,
    note: '当前事件类别',
    state: riskLevel.value === 'high' ? 'danger' : 'warning',
  },
  {
    key: 'trace',
    title: '根因溯源',
    value: labelName(topPath.value?.defect_mechanism) || '待定位',
    note: labelName(topPath.value?.equipment_zone) || '全流程',
    state: 'active',
  },
  {
    key: 'evidence',
    title: '证据融合',
    value: `${evidenceCount.value} 条依据`,
    note: '生产/图谱/文本/规则',
    state: 'active',
  },
  {
    key: 'action',
    title: '处置闭环',
    value: actionText.value,
    note: '检查、调整、复核归档',
    state: 'normal',
  },
]);

function labelName(value?: string) {
  return value ? formatSteelTerm(value, props.labels) : '';
}

function statusName(status: ProcessStepStatus['status']) {
  const map: Record<ProcessStepStatus['status'], string> = {
    context: '上游关联',
    normal: '稳定',
    active: '当前关注',
    warning: '预警',
    danger: '高风险',
  };
  return map[status] || status;
}
</script>

<style scoped>
.process-card {
  position: relative;
  min-height: 560px;
  overflow: hidden;
  border: 1px solid rgba(39, 212, 255, 0.18);
  border-radius: 10px;
  padding: 20px;
  background-image:
    linear-gradient(90deg, rgba(5, 12, 22, 0.78), rgba(5, 12, 22, 0.28) 48%, rgba(5, 12, 22, 0.78)),
    linear-gradient(180deg, rgba(5, 12, 22, 0.76), rgba(5, 12, 22, 0.18) 48%, rgba(5, 12, 22, 0.92)),
    url('/steel_realtime_process_bg.png');
  background-position: center;
  background-size: cover;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.32);
}

.process-card::before {
  position: absolute;
  inset: 0;
  content: '';
  background:
    linear-gradient(90deg, transparent, rgba(39, 212, 255, 0.14), transparent),
    radial-gradient(circle at 72% 32%, rgba(39, 212, 255, 0.16), transparent 34%);
  opacity: 0.72;
  animation: scan 4.8s linear infinite;
}

.process-card__head,
.live-summary,
.monitor-chain,
.process-rail {
  position: relative;
  z-index: 1;
}

.process-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.process-card h2 {
  margin: 0;
  color: #f0f7ff;
  font-size: 20px;
}

.process-card p {
  margin: 6px 0 0;
  color: #9bb4cc;
}

.scope-badge {
  border: 1px solid rgba(48, 209, 128, 0.44);
  border-radius: 999px;
  padding: 6px 10px;
  color: #a9ffd1;
  background: rgba(48, 209, 128, 0.09);
  white-space: nowrap;
}

.live-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 72px;
  border: 1px solid rgba(39, 212, 255, 0.18);
  border-radius: 10px;
  padding: 12px;
  background: rgba(5, 18, 32, 0.74);
  backdrop-filter: blur(8px);
}

.event-chip,
.summary-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.event-chip b,
.event-chip small {
  display: block;
}

.event-chip small,
.summary-metrics span {
  color: #9bb4cc;
  font-size: 12px;
}

.summary-metrics span {
  border: 1px solid rgba(142, 165, 189, 0.24);
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(7, 21, 37, 0.78);
}

.pulse-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #30d180;
  box-shadow: 0 0 18px #30d180;
}

.pulse-dot.is-medium {
  background: #f4bc45;
  box-shadow: 0 0 18px #f4bc45;
}

.pulse-dot.is-high {
  background: #ff5c65;
  box-shadow: 0 0 18px #ff5c65;
}

.monitor-chain {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.chain-stage {
  position: relative;
  min-height: 132px;
  border: 1px solid rgba(39, 212, 255, 0.24);
  border-radius: 10px;
  padding: 12px;
  background: rgba(5, 18, 32, 0.82);
  backdrop-filter: blur(8px);
}

.chain-stage:not(:last-child)::after {
  position: absolute;
  top: 50%;
  right: -15px;
  z-index: 2;
  width: 18px;
  height: 2px;
  content: '';
  background: #27d4ff;
  box-shadow: 0 0 14px #27d4ff;
}

.stage-index,
.chain-stage b,
.chain-stage strong,
.chain-stage small {
  display: block;
}

.stage-index {
  color: #5bdfff;
  font-size: 12px;
}

.chain-stage b {
  margin-top: 8px;
  color: #e7f0fb;
}

.chain-stage strong {
  display: -webkit-box;
  min-height: 42px;
  margin-top: 8px;
  overflow: hidden;
  color: #fff;
  font-size: 15px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.chain-stage small {
  margin-top: 8px;
  color: #9bb4cc;
  font-size: 12px;
}

.chain-stage.is-high,
.chain-stage.is-danger {
  border-color: rgba(255, 92, 101, 0.56);
  box-shadow: inset 0 0 0 1px rgba(255, 92, 101, 0.14);
}

.chain-stage.is-medium,
.chain-stage.is-warning {
  border-color: rgba(244, 188, 69, 0.52);
}

.chain-stage.is-active {
  border-color: rgba(39, 212, 255, 0.58);
}

.process-rail {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
  margin-top: 18px;
}

.process-node {
  min-height: 92px;
  border: 1px solid rgba(47, 85, 120, 0.86);
  border-radius: 8px;
  padding: 10px;
  color: #e7f0fb;
  text-align: left;
  background: rgba(5, 18, 32, 0.76);
  backdrop-filter: blur(6px);
  cursor: pointer;
}

.node-name,
.node-note,
.node-status {
  display: block;
}

.node-name {
  font-weight: 700;
}

.node-note,
.node-status {
  margin-top: 7px;
  color: #9bb4cc;
  font-size: 12px;
}

.is-warning {
  border-color: #f4bc45;
}

.is-danger {
  border-color: #ff5c65;
  box-shadow: 0 0 24px rgba(255, 92, 101, 0.2);
}

.is-active {
  border-color: #30d180;
}

.is-context {
  opacity: 0.76;
}

@keyframes scan {
  from {
    transform: translateX(-100%);
  }

  to {
    transform: translateX(100%);
  }
}

@media (max-width: 1280px) {
  .live-summary {
    align-items: flex-start;
    flex-direction: column;
    margin-top: 40px;
  }

  .monitor-chain,
  .process-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chain-stage:not(:last-child)::after {
    display: none;
  }
}
</style>
