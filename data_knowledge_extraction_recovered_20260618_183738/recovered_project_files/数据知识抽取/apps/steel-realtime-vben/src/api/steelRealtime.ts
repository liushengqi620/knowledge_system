import type {
  AssistantPathResponse,
  CaseKnowledgeIngestResponse,
  CascadeModelSummary,
  CascadeRowsResponse,
  DataSourcesResponse,
  EvidencePackage,
  IngestResponse,
  KnowledgeEntity,
  KnowledgeCandidateValidationResponse,
  KgEventSubgraph,
  KgGovernanceActionResponse,
  KgVersionResponse,
  KnowledgeGraphSummary,
  KnowledgeItem,
  KnowledgeRelation,
  ModelRunSummary,
  NextEventResponse,
  PathLibraryItem,
  SteelRealtimeEvent,
  SteelRealtimeSeed,
  SystemArtifact,
} from '../types/steelRealtime';

const API_BASE = import.meta.env.VITE_STEEL_REALTIME_API_BASE || '';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Steel realtime API ${response.status}: ${path}`);
  }
  return response.json() as Promise<T>;
}

export function getSteelRealtimeSeed(): Promise<SteelRealtimeSeed> {
  return requestJson<SteelRealtimeSeed>('/api/seed');
}

export function getNextRealtimeEvent(cursor: number): Promise<NextEventResponse> {
  return requestJson<NextEventResponse>(`/api/realtime/next?cursor=${cursor}`);
}

export function connectRealtimeStream(
  cursor: number,
  onEvent: (payload: NextEventResponse) => void,
): EventSource {
  const source = new EventSource(`${API_BASE}/api/realtime/stream?cursor=${cursor}&limit=20`);
  source.addEventListener('steel-event', ((event: MessageEvent) => {
    onEvent(JSON.parse(event.data) as NextEventResponse);
  }) as EventListener);
  return source;
}

export function getRiskEvents(): Promise<{ events: SteelRealtimeEvent[]; n_events: number }> {
  return requestJson<{ events: SteelRealtimeEvent[]; n_events: number }>('/risk/events');
}

export function getEventDetail(eventId: string): Promise<SteelRealtimeEvent> {
  return requestJson<SteelRealtimeEvent>(`/api/events/${encodeURIComponent(eventId)}`);
}

export function getIdentification(eventId: string) {
  return requestJson(`/identify/events/${encodeURIComponent(eventId)}`);
}

export function getTraceability(eventId: string) {
  return requestJson(`/api/trace/events/${encodeURIComponent(eventId)}`);
}

export function getRecommendation(eventId: string) {
  return requestJson(`/api/recommend/events/${encodeURIComponent(eventId)}`);
}

export function searchKnowledge(query: string): Promise<{ query: string; items: KnowledgeItem[] }> {
  return requestJson<{ query: string; items: KnowledgeItem[] }>(
    `/api/knowledge/search?q=${encodeURIComponent(query)}`,
  );
}

export function ingestRealtimeEvent(payload: Record<string, unknown>): Promise<IngestResponse> {
  return requestJson<IngestResponse>('/api/realtime/ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function askAssistantPathQuestion(payload: {
  event_id?: string;
  path_index?: number;
  question: string;
}): Promise<AssistantPathResponse> {
  return requestJson<AssistantPathResponse>('/api/assistant/path-question', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getDataSources(): Promise<DataSourcesResponse> {
  return requestJson<DataSourcesResponse>('/api/data/sources');
}

export function getDataEvents(): Promise<{ events: SteelRealtimeEvent[]; n_events: number }> {
  return requestJson<{ events: SteelRealtimeEvent[]; n_events: number }>('/api/data/events');
}

export function uploadStructuredData(payload: Record<string, unknown>) {
  return requestJson('/api/data/structured/upload', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function uploadTextData(payload: Record<string, unknown>) {
  return requestJson('/api/data/text/upload', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function buildEventDataset(payload: Record<string, unknown>) {
  return requestJson('/api/data/events/build', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function createKnowledgeExtractionJob(payload: Record<string, unknown>) {
  return requestJson('/api/knowledge/extraction/jobs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getKgSummary(): Promise<KnowledgeGraphSummary> {
  return requestJson<KnowledgeGraphSummary>('/api/kg/summary');
}

export function getKgNodes(): Promise<{ nodes: KnowledgeEntity[] }> {
  return requestJson<{ nodes: KnowledgeEntity[] }>('/api/kg/nodes');
}

export function getKgEdges(): Promise<{ edges: KnowledgeRelation[] }> {
  return requestJson<{ edges: KnowledgeRelation[] }>('/api/kg/edges');
}

export function getKgSubgraph(query = ''): Promise<{ query: string; nodes: KnowledgeEntity[]; edges: KnowledgeRelation[] }> {
  return requestJson<{ query: string; nodes: KnowledgeEntity[]; edges: KnowledgeRelation[] }>(
    `/api/kg/subgraph?q=${encodeURIComponent(query)}`,
  );
}

export function getKgPathLibrary(): Promise<{ paths: PathLibraryItem[] }> {
  return requestJson<{ paths: PathLibraryItem[] }>('/api/kg/path-library');
}

export function getKgEvidence(eventId: string): Promise<EvidencePackage> {
  return requestJson<EvidencePackage>(`/api/kg/evidence/${encodeURIComponent(eventId)}`);
}

export function getKgEventSubgraph(eventId: string, hops = 1): Promise<KgEventSubgraph> {
  return requestJson<KgEventSubgraph>(`/api/kg/event-subgraph/${encodeURIComponent(eventId)}?hops=${hops}`);
}

export function getKgVersions(): Promise<KgVersionResponse> {
  return requestJson<KgVersionResponse>('/api/kg/versions');
}

export function createCaseKnowledgeIngest(payload: {
  event_id?: string;
  path_index?: number;
  feedback?: string;
  review_status?: string;
}): Promise<CaseKnowledgeIngestResponse> {
  return requestJson<CaseKnowledgeIngestResponse>('/api/kg/case-ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function submitKgGovernanceAction(payload: {
  action_type: 'mark_review_required' | 'request_merge' | 'publish_candidate' | string;
  target_type: 'knowledge_node' | 'knowledge_relation' | string;
  target_id?: string;
  decision?: string;
  note?: string;
}): Promise<KgGovernanceActionResponse> {
  return requestJson<KgGovernanceActionResponse>('/api/kg/governance/actions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function validateKnowledgeCandidate(payload: CaseKnowledgeIngestResponse): Promise<KnowledgeCandidateValidationResponse> {
  return requestJson<KnowledgeCandidateValidationResponse>('/api/knowledge/candidates/validate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getModelRuns(): Promise<{ runs: ModelRunSummary[] }> {
  return requestJson<{ runs: ModelRunSummary[] }>('/api/model/runs');
}

export function getCascadeModelSummary(): Promise<CascadeModelSummary> {
  return requestJson<CascadeModelSummary>('/api/model/cascade/summary');
}

export function getCascadePredictions(limit = 20, onlyAbnormal = false): Promise<CascadeRowsResponse> {
  return requestJson<CascadeRowsResponse>(
    `/api/model/cascade/predictions?limit=${limit}&only_abnormal=${String(onlyAbnormal)}`,
  );
}

export function getTraceabilityEvidenceRows(limit = 20, onlyAbnormal = true): Promise<CascadeRowsResponse> {
  return requestJson<CascadeRowsResponse>(
    `/api/model/traceability/evidence?limit=${limit}&only_abnormal=${String(onlyAbnormal)}`,
  );
}

export function createModelRun(payload: Record<string, unknown>): Promise<ModelRunSummary> {
  return requestJson<ModelRunSummary>('/api/model/runs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getEvaluationSummary(): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>('/api/evaluation/summary');
}

export function getEvidenceQuality(): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>('/api/evaluation/evidence-quality');
}

export function getSystemArtifacts(): Promise<{ artifacts: SystemArtifact[] }> {
  return requestJson<{ artifacts: SystemArtifact[] }>('/api/system/artifacts');
}
