export type RiskLevel = 'low' | 'medium' | 'high';

export interface ProcessStepStatus {
  id: string;
  name: string;
  scope: 'context' | 'model';
  status: 'context' | 'normal' | 'active' | 'warning' | 'danger';
  note: string;
}

export interface RiskWarning {
  risk_label: number;
  risk_probability: number;
  risk_level: RiskLevel;
  boundary_status: string;
  inference_status?: string;
}

export interface AbnormalIdentification {
  primary_abnormal_class?: string;
  predicted_abnormal_groups: string[];
  display_groups?: string[];
  multilabel_probability: Record<string, number>;
  class_confidence?: number;
  ambiguous_flag?: boolean;
  inference_status?: string;
}

export interface TraceNode {
  id: string;
  label: string;
  layer: string;
}

export interface EvidenceSource {
  source_id: string;
  source_type: 'structured_production' | 'knowledge_graph' | 'text_knowledge' | 'expert_rule' | string;
  title: string;
  confidence: number;
  snippet: string;
}

export interface TracePath {
  feature: string;
  feature_value?: number | string | null;
  variable_group: string;
  equipment_zone: string;
  defect_mechanism: string;
  path_score: number;
  path_occlusion_drop: number;
  nodes: TraceNode[];
  graph_prior?: number;
  graph_relation_score?: number;
  path_library_score?: number;
  path_library_match?: boolean;
  path_library_event_count?: number;
  text_evidence?: string[];
  model_attribution?: number;
  temporal_consistency?: number;
  expert_rule_alignment?: number;
  final_score?: number;
  process_consistency?: number;
  score_model?: string;
  score_components?: Record<string, unknown>;
  graph_evidence_detail?: {
    matched_relation_count?: number;
    matched_relations?: Array<Record<string, unknown>>;
    source_types?: string[];
    snippets?: string[];
    path_library_key?: string;
  };
  canonical_path?: Record<string, unknown>;
  evidence_sources?: EvidenceSource[];
  inference_status?: string;
}

export interface EvidencePackage {
  event_id: string;
  evidence_role: string;
  structured_signal: Record<string, unknown>;
  graph_evidence: Record<string, unknown>;
  text_evidence: Array<Record<string, unknown>>;
  evidence_sources: EvidenceSource[];
  assistant_policy: string;
  kg_fusion_summary?: KgFusionSummary;
}

export interface KgFusionSummary {
  mapped_entity_count: number;
  event_subgraph_node_count: number;
  event_subgraph_edge_count: number;
  missing_link_count: number;
  graph_path_hit_count: number;
  avg_graph_prior: number;
  avg_final_score: number;
  score_delta_after_kg: number;
  focus_node_ids: string[];
  matched_path_ids: string[];
  role: string;
}

export interface KgEventSubgraph {
  event_id?: string;
  hops: number;
  focus_node_ids: string[];
  nodes: KnowledgeEntity[];
  edges: KnowledgeRelation[];
  missing_links: Array<{
    source: string;
    target: string;
    relation_type: string;
    label: string;
  }>;
  matched_path_ids: string[];
}

export interface KgVersionResponse {
  current_version: Record<string, unknown>;
  candidate_store: Record<string, unknown>;
  recent_actions: Array<Record<string, unknown>>;
}

export interface KgGovernanceActionResponse {
  action_id: string;
  created_at: string;
  action_type: string;
  target_type: string;
  target_id: string;
  decision: string;
  note: string;
  operator: string;
  status: string;
  next_step: string;
}

export interface Traceability {
  reason_mechanism_set?: string;
  reason_variable_group_set?: string;
  reason_stage_set?: string;
  top_k_paths: TracePath[];
  evidence_package?: EvidencePackage;
}

export interface Recommendation {
  risk_summary: string;
  recommended_checks: string[];
  recommended_adjustments: string[];
  verification_actions?: string[];
  evidence_binding?: string;
  inference_status?: string;
}

export interface SteelRealtimeEvent {
  event_id: string;
  sequence_no: number;
  timestamp?: string;
  line_id?: string;
  process_status: ProcessStepStatus[];
  risk_warning: RiskWarning;
  abnormal_identification: AbnormalIdentification;
  traceability: Traceability;
  recommendation: Recommendation;
  kg_fusion?: KgFusionSummary;
}

export interface KnowledgeItem {
  id?: string;
  type?: string;
  key?: string;
  title: string;
  scope?: string;
  keywords?: string[];
  evidence_type?: string;
  source_type?: string;
  relation_type?: string;
  content?: string;
  summary?: string;
  confidence?: number;
  event_count?: number;
  evidence_count?: number;
  feature_label?: string;
}

export interface AssistantPathResponse {
  event_id?: string;
  path_index: number;
  llm_role: string;
  llm_runtime?: {
    enabled: boolean;
    status: string;
    base_url?: string;
    model?: string;
    error?: string;
  };
  answer: string;
  knowledge_items: KnowledgeItem[];
  selected_path?: TracePath;
}

export interface StructuredDataSource {
  id: string;
  name: string;
  source_type: string;
  status: string;
  records?: number;
  fields?: string[];
  alignment_keys?: string[];
}

export interface TextKnowledgeSource {
  id: string;
  name: string;
  source_type: string;
  status: string;
  documents?: number;
  extraction_scope?: string[];
}

export interface DataSourcesResponse {
  structured_sources: StructuredDataSource[];
  text_sources: TextKnowledgeSource[];
  field_mapping: Array<Record<string, unknown>>;
  event_window_dataset: Record<string, unknown>;
  quality_checks: Record<string, unknown>;
}

export interface KnowledgeEntity {
  id: string;
  label: string;
  entity_type: string;
  source_type: string;
  source_types?: string[];
  confidence: number;
  review_status: string;
  canonical_key?: string;
  aliases?: string[];
  disambiguation_rule?: string;
  evidence_count?: number;
}

export interface KnowledgeRelation {
  id: string;
  source: string;
  target: string;
  relation_type: string;
  label: string;
  confidence: number;
  source_type: string;
  source_types?: string[];
  evidence_snippet: string;
  evidence_snippets?: string[];
  evidence_count?: number;
}

export interface CaseKnowledgeIngestResponse {
  batch_id: string;
  status: string;
  event_id?: string;
  review_status: string;
  target_graph: string;
  merge_policy: string;
  model_fusion_role: string;
  selected_path?: TracePath;
  candidate_entities: KnowledgeEntity[];
  candidate_relations: KnowledgeRelation[];
  evidence_sources: EvidenceSource[];
  feedback?: string;
}

export interface CandidateValidationItem {
  candidate_id: string;
  candidate_label: string;
  candidate_type?: string;
  relation_type?: string;
  source?: string;
  target?: string;
  decision: string;
  action: string;
  top_score?: number;
  matches: Array<Record<string, unknown>>;
}

export interface KnowledgeCandidateValidationResponse {
  batch_id?: string;
  status: string;
  recommendation: string;
  summary: {
    candidate_entity_count: number;
    candidate_relation_count: number;
    suggested_merge_count: number;
    suggested_new_count: number;
    review_required_count: number;
    conflict_count: number;
  };
  entity_results: CandidateValidationItem[];
  relation_results: CandidateValidationItem[];
  validation_rules: string[];
}

export interface KnowledgeGraphSummary {
  node_count: number;
  edge_count: number;
  path_template_count: number;
  node_type_counts: Record<string, number>;
  relation_type_counts: Record<string, number>;
  mechanism_coverage: string[];
  fusion_role: string;
  connectivity?: {
    isolated_node_count: number;
    low_degree_node_count: number;
    isolated_node_rate: number;
    low_degree_node_rate: number;
    avg_degree: number;
    isolated_node_ids: string[];
  };
  entity_disambiguation?: {
    policy: string;
    node_merge_count: number;
    edge_merge_count: number;
    rule_count: number;
  };
}

export interface KnowledgeDisambiguationRule {
  rule_id: string;
  name: string;
  description: string;
  examples?: string[];
}

export interface KnowledgeDisambiguationSummary {
  policy: string;
  node_merge_count: number;
  edge_merge_count: number;
  rule_count: number;
  rules: KnowledgeDisambiguationRule[];
  top_merged_nodes: Array<{
    id: string;
    label: string;
    entity_type: string;
    evidence_count: number;
    aliases: string[];
  }>;
  top_merged_edges: Array<{
    id: string;
    source: string;
    target: string;
    relation_type: string;
    evidence_count: number;
    confidence: number;
  }>;
}

export interface KnowledgeGraphBundle {
  backend: string;
  summary: KnowledgeGraphSummary;
  nodes: KnowledgeEntity[];
  edges: KnowledgeRelation[];
  path_library: PathLibraryItem[];
  disambiguation?: KnowledgeDisambiguationSummary;
}

export interface KnowledgeExtractionJob {
  job_id: string;
  status: string;
  input_sources: string[];
  extractors: string[];
  entity_count: number;
  relation_count: number;
  output_target: string;
}

export interface KnowledgeExtractionBundle {
  jobs: KnowledgeExtractionJob[];
  entities: KnowledgeEntity[];
  relations: KnowledgeRelation[];
}

export interface PathLibraryItem {
  path_id: string;
  variable_group: string;
  equipment_zone: string;
  defect_mechanism: string;
  mechanism_label: string;
  event_count: number;
  avg_final_score: number;
  evidence_types: string[];
}

export interface ModelRunSummary {
  run_id: string;
  model_contract: string;
  status: string;
  algorithm_status: string;
  input_artifacts: string[];
  output_artifacts: string[];
  event_count: number;
  kg_node_count?: number;
  kg_edge_count?: number;
  scoring_model?: string;
  test_metrics?: Record<string, number>;
  gate_policy?: Record<string, unknown>;
  artifact_dir?: string;
}

export interface CascadeStage {
  stage: string;
  name: string;
  output: string;
  metric: Record<string, unknown>;
}

export interface CascadeModelSummary {
  status: string;
  model_contract: string;
  pipeline: CascadeStage[];
  metrics: {
    binary_test?: Record<string, number>;
    multiclass_test?: Record<string, number>;
    multilabel_test?: Record<string, unknown>;
  };
  dataset: Record<string, unknown>;
  features: {
    original_count?: number;
    kept_count?: number;
    dropped_correlated_count?: number;
    top_global_features?: Array<Record<string, unknown>>;
    module_importance?: Array<Record<string, unknown>>;
  };
  gate_policy: {
    name?: string;
    normal_rule?: string;
    abnormal_rule?: string;
  };
  artifacts: Record<string, string>;
  preview: Array<Record<string, unknown>>;
  traceability_evidence_preview: Array<Record<string, unknown>>;
}

export interface CascadeRowsResponse {
  source: string;
  rows: Array<Record<string, unknown>>;
}

export interface EvaluationBundle {
  summary: Record<string, unknown>;
  evidence_quality: Record<string, unknown>;
}

export interface SystemArtifact {
  artifact_id: string;
  name: string;
  path: string;
  status: string;
}

export interface SteelRealtimeSeed {
  system_name: string;
  template: string;
  realtime_mode: string;
  process_steps: ProcessStepStatus[];
  display_labels: Record<string, string>;
  metrics: Record<string, unknown>;
  summary: Record<string, unknown>;
  knowledge_items?: KnowledgeItem[];
  events: SteelRealtimeEvent[];
  data_sources?: DataSourcesResponse;
  knowledge_extraction?: KnowledgeExtractionBundle;
  knowledge_graph?: KnowledgeGraphBundle;
  model_runs?: ModelRunSummary[];
  evaluation?: EvaluationBundle;
  system_artifacts?: SystemArtifact[];
}

export interface NextEventResponse {
  cursor: number;
  event: SteelRealtimeEvent;
}

export interface IngestResponse {
  status: 'accepted';
  event: SteelRealtimeEvent;
  n_events: number;
}
