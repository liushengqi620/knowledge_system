<template>
  <section class="stream-card">
    <div class="stream-card__head">
      <div>
        <h2>产线实时告警</h2>
        <p>按时间推送质量风险事件，点击后进入当前处置链路</p>
      </div>
      <span :class="['stream-state', running ? 'is-running' : '']">
        {{ running ? '数据流运行中' : '数据流待启动' }}
      </span>
    </div>
    <div class="event-list">
      <button
        v-for="event in events"
        :key="event.event_id"
        :class="['event-row', { active: event.event_id === activeEventId }]"
        type="button"
        @click="$emit('select-event', event.event_id)"
      >
        <strong>{{ eventTitle(event) }}</strong>
        <span class="event-meta">
          <i>{{ lineName(event.line_id) }}</i>
          <i :class="['risk-chip', riskLevelClass(event.risk_warning?.risk_level)]">
            {{ riskLevelName(event.risk_warning?.risk_level) }}
          </i>
          <i>风险 {{ formatPercent(event.risk_warning?.risk_probability) }}</i>
        </span>
        <small>{{ eventSummary(event) }}</small>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SteelRealtimeEvent } from '../types/steelRealtime';
import {
  eventDisplayTitle,
  eventTitle as formatEventTitle,
  formatSteelTerm,
  lineName,
  riskLevelName,
} from '../utils/steelTerminology';

const props = defineProps<{
  events: SteelRealtimeEvent[];
  activeEventId?: string;
  labels?: Record<string, string>;
  running: boolean;
}>();

defineEmits<{
  (event: 'select-event', eventId: string): void;
}>();

function formatPercent(value?: number) {
  return typeof value === 'number' ? `${Math.round(value * 100)}%` : '-';
}

function riskLevelClass(level?: string) {
  return level ? `is-${level}` : 'is-low';
}

function labelName(value?: string) {
  return value ? formatSteelTerm(value, props.labels) : '';
}

function displayGroup(event: SteelRealtimeEvent) {
  const raw = event.abnormal_identification?.display_groups?.[0]
    || event.abnormal_identification?.primary_abnormal_class
    || event.abnormal_identification?.predicted_abnormal_groups?.[0]
    || '';
  return labelName(raw) || '质量异常';
}

function eventTitle(event: SteelRealtimeEvent) {
  return eventDisplayTitle(event, props.labels) || formatEventTitle(event, props.labels);
}

function displayGroups(event: SteelRealtimeEvent) {
  const groups = event.abnormal_identification?.display_groups?.length
    ? event.abnormal_identification.display_groups
    : event.abnormal_identification?.predicted_abnormal_groups || [];
  return groups.map((item) => labelName(item)).filter(Boolean);
}

function eventSummary(event: SteelRealtimeEvent) {
  const groups = displayGroups(event).join('、') || displayGroup(event);
  return `当前识别：${groups}`;
}
</script>

<style scoped>
.stream-card {
  position: relative;
  min-height: 360px;
  overflow: hidden;
  border: 1px solid rgba(36, 64, 95, 0.9);
  border-radius: 10px;
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(13, 27, 47, 0.9), rgba(7, 17, 31, 0.94)),
    linear-gradient(90deg, rgba(7, 17, 31, 0.55), rgba(7, 17, 31, 0.88)),
    url('/steel_realtime_workshop_bg.png');
  background-position: center;
  background-size: cover;
}

.stream-card::before {
  position: absolute;
  inset: 0;
  content: '';
  background: linear-gradient(90deg, transparent, rgba(39, 212, 255, 0.12), transparent);
  animation: streamScan 4s linear infinite;
}

.stream-card > * {
  position: relative;
  z-index: 1;
}

.stream-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stream-card h2 {
  margin: 0;
  color: #e7f0fb;
  font-size: 18px;
}

.stream-card p {
  margin: 5px 0 0;
  color: #8ea5bd;
  font-size: 12px;
}

.stream-state {
  border: 1px solid rgba(142, 165, 189, 0.35);
  border-radius: 999px;
  padding: 5px 9px;
  color: #8ea5bd;
  font-size: 12px;
}

.stream-state.is-running {
  border-color: rgba(48, 209, 128, 0.5);
  color: #a9ffd1;
}

.event-list {
  display: grid;
  gap: 8px;
  max-height: 286px;
  margin-top: 14px;
  overflow: auto;
}

.event-row {
  border: 1px solid #24405f;
  border-radius: 8px;
  padding: 10px;
  color: #d8e6f5;
  text-align: left;
  background: #071525;
  cursor: pointer;
}

.event-row.active,
.event-row:hover {
  border-color: #27d4ff;
  background: rgba(39, 212, 255, 0.12);
}

.event-row strong,
.event-row span,
.event-row small {
  display: block;
}

.event-meta {
  display: flex !important;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.event-meta i,
.event-row small {
  color: #8ea5bd;
  font-size: 12px;
  font-style: normal;
}

.event-meta i {
  border: 1px solid rgba(142, 165, 189, 0.22);
  border-radius: 999px;
  padding: 3px 7px;
  background: rgba(7, 21, 37, 0.72);
}

.risk-chip.is-high {
  border-color: rgba(255, 92, 101, 0.55);
  color: #ffd5d8;
}

.risk-chip.is-medium {
  border-color: rgba(244, 188, 69, 0.55);
  color: #ffe3a3;
}

.risk-chip.is-low {
  border-color: rgba(48, 209, 128, 0.5);
  color: #a9ffd1;
}

.event-row small {
  margin-top: 7px;
}

@keyframes streamScan {
  from {
    transform: translateX(-100%);
  }

  to {
    transform: translateX(100%);
  }
}
</style>
