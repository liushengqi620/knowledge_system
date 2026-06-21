import type { SteelRealtimeEvent, TracePath } from '../types/steelRealtime';

export const STEEL_TERM_LABELS: Record<string, string> = {
  timestamp: '采集时间',
  line_id: '产线',
  heat_no: '炉号',
  batch_id: '批次号',
  process_step: '工序',
  event_window: '事件窗口',
  event_precursor_window: '异常前序窗口',
  process_variable: '工艺变量',
  quality_label: '质量判定',

  roughing: '粗炼',
  refining: '精炼',
  tundish: '中间包',
  mold: '结晶器',
  flow_control: '流量控制',
  heat_transfer: '传热/冷却',
  quality: '品质检测',
  mold_heat_transfer: '结晶器传热',
  nozzle_flow: '水口/流量',

  temperature: '温度制度',
  mold_level: '结晶器液位',
  casting_speed: '拉速',
  cooling_water: '二冷水量',
  tundish_weight: '中间包吨位',
  sequence_transition: '过渡段序列',
  heat_exchange: '热交换',
  ems_taper_oscillation: '结晶器锥度/振动',
  flux: '保护渣',
  heat_transfer_uniformity: '传热均匀性',
  flow_control_stability: '流量控制稳定性',
  process_operation: '工艺操作状态',
  tundish_transition: '中间包过渡状态',
  mold_level_stability: '结晶器液位稳定性',
  oscillation_ems_state: '振动/电磁搅拌状态',
  slag_flux_state: '保护渣状态',
  thermal_state: '热工状态',

  temperature_flux: '温度/保护渣异常',
  mold_level_slag_risk: '液面/卷渣风险',
  speed_stopper_flow: '拉速/塞棒/流量异常',
  process_fluctuation: '过程参数波动',
  heat_transfer_imbalance: '传热不均',
  transition_tundish: '过渡/中间包状态',
  other_quality_abnormal: '其他质量异常',

  window_feature: '窗口变量',
  variable_group: '变量组',
  equipment_zone: '工序区域',
  process_state: '工艺状态',
  defect_mechanism: '异常机理',
  event_quality_class: '异常类别',
  correction_action: '纠正建议',

  mean: '平均值',
  std: '波动',
  trend: '趋势',
  last: '末值',
  max: '最大值',
  min: '最小值',
};

const FEATURE_BASE_LABELS: Record<string, string> = {
  TD_avg_temp: '中包平均温度',
  cover_flux_1: '保护渣消耗波动',
  heat_exchange_ew_diff: '结晶器东西侧热交换差',
  heat_exchange_mean: '结晶器热交换均值',
  liquidus_temp: '液相线温度',
  mold_level_ge7: '液面大波动次数',
  mold_level_mean: '结晶器液面均值',
  mold_level_range: '结晶器液面波动范围',
  superheat: '钢水过热度',
};

const STATUS_LABELS: Record<string, string> = {
  context: '上游关联',
  normal: '稳定',
  active: '当前关注',
  warning: '预警',
  danger: '高风险',
  loaded: '已加载',
  pending_backend_validation: '待后端校验',
  backend_archive_only: '后端归档',
  human_review_required: '需人工审核',
  pending_manual_review: '待人工审核',
  pending_feedback_completion: '待补充反馈',
  system_seed: '系统基线',
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  structured_production: '生产实时信号',
  knowledge_graph: '知识图谱证据',
  text_knowledge: '文本知识证据',
  expert_rule: '专家规则',
  expert_seed: '专家经验基线',
  system_seed: '系统基线',
};

const ENTITY_TYPE_LABELS: Record<string, string> = {
  process_step: '工序实体',
  window_feature: '时间窗口变量',
  variable_group: '变量组',
  equipment_zone: '设备/工序区域',
  defect_mechanism: '异常机理',
  correction_action: '处置建议',
};

const RELATION_TYPE_LABELS: Record<string, string> = {
  HAS_RISK_MECHANISM: '工序关联风险机理',
  BELONGS_TO_VARIABLE_GROUP: '变量归属',
  OBSERVED_IN_ZONE: '变量观测区域',
  INDICATES_MECHANISM: '变量指向异常机理',
};

const UNIT_LABELS: Record<string, string> = {
  mm: '毫米',
  t: '吨',
  'L/min': '升/分钟',
  '℃': '摄氏度',
  s: '秒',
  min: '分钟',
};

const SEGMENT_LABELS: Record<string, string> = {
  ems: '电磁搅拌',
  taper: '锥度',
  oscillation: '振动',
  heat: '传热',
  transfer: '传递',
  imbalance: '不均',
  exchange: '热交换',
  nozzle: '水口',
  flow: '流量',
  tundish: '中间包',
  weight: '吨位',
  sequence: '过渡段',
  transition: '过渡',
  mold: '结晶器',
  level: '液位',
  slag: '卷渣',
  risk: '风险',
  speed: '拉速',
  stopper: '塞棒',
  temperature: '温度',
  flux: '保护渣',
  process: '过程',
  fluctuation: '波动',
  operation: '操作',
  stability: '稳定性',
  uniformity: '均匀性',
};

export function formatSteelTerm(value: unknown, labels?: Record<string, string>): string {
  if (value == null || value === '') return '-';
  if (typeof value === 'number') return value.toFixed(3);
  const raw = String(value);
  if (labels?.[raw]) return labels[raw];
  if (STEEL_TERM_LABELS[raw]) return STEEL_TERM_LABELS[raw];
  return readableFallback(raw);
}

export function riskLevelName(level?: string): string {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
  };
  return (level && map[level]) || level || '-';
}

export function lineName(lineId?: string): string {
  const map: Record<string, string> = {
    'line-A': 'A线连铸',
    'line-B': 'B线连铸',
    line_A: 'A线连铸',
    line_B: 'B线连铸',
  };
  return (lineId && map[lineId]) || lineId || 'A线连铸';
}

export function sequenceName(sequence?: number): string {
  return typeof sequence === 'number' ? `#${String(sequence + 1).padStart(3, '0')}` : '#---';
}

export function primaryEventClass(event?: SteelRealtimeEvent): string {
  return event?.abnormal_identification?.display_groups?.[0]
    || event?.abnormal_identification?.primary_abnormal_class
    || event?.abnormal_identification?.predicted_abnormal_groups?.[0]
    || '';
}

export function eventTitle(event?: SteelRealtimeEvent, labels?: Record<string, string>): string {
  if (!event) return '-';
  const primary = formatSteelTerm(primaryEventClass(event), labels) || '质量异常';
  return `${primary} ${sequenceName(event.sequence_no)}`;
}

export function eventDisplayTitle(event?: SteelRealtimeEvent, labels?: Record<string, string>): string {
  if (!event) return '-';
  const primary = formatSteelTerm(primaryEventClass(event), labels) || '质量异常';
  return `事件 ${sequenceName(event.sequence_no)}｜${primary}`;
}

export function tracePathTitle(path?: TracePath, index = 0, labels?: Record<string, string>): string {
  if (!path) return `原因 ${index + 1}`;
  const zone = formatSteelTerm(path.equipment_zone, labels);
  const mechanism = formatSteelTerm(path.defect_mechanism, labels);
  return `原因 ${index + 1}｜${zone}：${mechanism}`;
}

export function tracePathSummary(path?: TracePath, labels?: Record<string, string>): string {
  if (!path) return '-';
  const feature = formatSteelTerm(path.feature, labels);
  const group = formatSteelTerm(path.variable_group, labels);
  return `关键变量：${feature}；信号组：${group}`;
}

export function formatSourceType(value?: string): string {
  return (value && SOURCE_TYPE_LABELS[value]) || formatSteelTerm(value);
}

export function formatEntityType(value?: string): string {
  return (value && ENTITY_TYPE_LABELS[value]) || formatSteelTerm(value);
}

export function formatRelationType(value?: string): string {
  return (value && RELATION_TYPE_LABELS[value]) || formatSteelTerm(value);
}

export function formatReviewStatus(value?: string): string {
  return (value && STATUS_LABELS[value]) || formatSteelTerm(value);
}

function readableFallback(raw: string): string {
  if (STATUS_LABELS[raw]) return STATUS_LABELS[raw];
  if (SOURCE_TYPE_LABELS[raw]) return SOURCE_TYPE_LABELS[raw];
  if (ENTITY_TYPE_LABELS[raw]) return ENTITY_TYPE_LABELS[raw];
  if (RELATION_TYPE_LABELS[raw]) return RELATION_TYPE_LABELS[raw];

  const eventMatch = raw.match(/^event[_-]?(\d+)[_-](.+)$/);
  if (eventMatch) {
    return `事件 #${eventMatch[1].padStart(3, '0')}｜${formatSteelTerm(eventMatch[2])}`;
  }

  const featureMatch = raw.match(/^(.+?)_(mean|std|trend|last|max|min)$/);
  if (featureMatch) {
    const [, base, statKey] = featureMatch;
    const stat = STEEL_TERM_LABELS[statKey] || statKey;
    const unitMatch = base.match(/^(.+?)\/(.+)$/);
    if (unitMatch) {
      const [, name, unit] = unitMatch;
      return `${name}（${formatUnit(unit)}，${stat}）`;
    }
    const baseLabel = featureBaseLabel(base);
    return `${baseLabel}（${stat}）`;
  }

  const [namePart, unitAndStat] = raw.split('/');
  const pieces = namePart.split(/[_\s-]+/).filter(Boolean);
  const translated = pieces.map((piece) => SEGMENT_LABELS[piece] || piece).join('');
  if (!unitAndStat) return translated || raw;

  const unitMatch = unitAndStat.match(/^(.+?)_(mean|std|trend|last|max|min)$/);
  if (unitMatch) {
    const unit = UNIT_LABELS[unitMatch[1]] || unitMatch[1];
    const stat = STEEL_TERM_LABELS[unitMatch[2]] || unitMatch[2];
    return `${translated}（${unit}，${stat}）`;
  }
  return `${translated}（${unitAndStat}）`;
}

function featureBaseLabel(raw: string): string {
  if (FEATURE_BASE_LABELS[raw]) return FEATURE_BASE_LABELS[raw];

  const unitMatch = raw.match(/^(.+?)\/(.+)$/);
  if (unitMatch) {
    const [, name, unit] = unitMatch;
    return `${name}（${formatUnit(unit)}）`;
  }

  const pieces = raw.split(/[_\s-]+/).filter(Boolean);
  return pieces.map((piece) => SEGMENT_LABELS[piece] || piece).join('') || raw;
}

function formatUnit(unit: string): string {
  const normalized = unit.replace(/^\((.*)\)$/, '$1');
  return UNIT_LABELS[normalized] || UNIT_LABELS[unit] || normalized;
}
