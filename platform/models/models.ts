export interface Task {
  id: string;
  created_at: number;
  project_id: string;
  session_id: string;
  input: string;
  additional_input?: Record<string, any>;
  output?: string;
  additional_output?: Record<string, any>;
  metadata?: Record<string, any>;
  data?: Record<string, any>;
  flag?: string;
  last_eval?: Eval;
  sentiment?: SentimentObject;
  language?: string;
  notes?: string;
}

export interface SentimentObject {
  score: number;
  magnitude: number;
  label: string;
}

export interface Eval {
  id: string;
  created_at: number;
  project_id: string;
  session_id: string;
  task_id: string;
  value: string;
  source: string;
  notes?: string | null;
}

export interface TaskWithEvents extends Task {
  events: Event[];
}

export interface UsageQuota {
  org_id: string;
  plan: string;
  current_usage: number;
  max_usage: number;
  max_usage_label: string;
}

export interface OrgMetadata {
  org_id: string;
  plan?: string | null; // "hobby" or "pro"
  customer_id?: string | null; // Stripe customer id
  initialized?: boolean | null; // Whether the org has been initialized
}

export interface Session {
  id: string;
  created_at: number;
  project_id: string;
  metadata?: Record<string, any>;
  data?: Record<string, any>;
  preview?: string;
  environment?: string;
  notes?: string;
  session_length?: number;
}

export interface SessionWithEvents extends Session {
  events: Event[];
}

export interface SessionWithEvents extends Session {
  tasks: Task[];
}

export interface UserMetadata {
  user_id: string;
  nb_tasks: number;
  avg_success_rate: number;
  avg_session_length: number;
  total_tokens: number;
  events: Event[];
  tasks_id: string[];
  sessions: Session[];
}

export interface ScoreRange {
  min: number;
  max: number;
  value: number;
  score_type: ScoreRangeType;
}

export interface Event {
  id: string;
  created_at: number;
  event_name: string;
  task_id?: string;
  session_id?: string;
  project_id: string;
  webhook?: string;
  source: string;
  score_range?: ScoreRange;
  confirmed: boolean;
}

export enum DetectionEngine {
  LLM = "llm_detection",
  KEYWORD = "keyword_detection",
  REGEX = "regex_detection",
  TF = "tf_detection"
}

export enum DetectionScope {
  Task = "task",
  Session = "session",
  TaskInputOnly = "task_input_only",
  TaskOutputOnly = "task_output_only",
}

export enum ScoreRangeType {
  confidence = "confidence",
  range = "range",
}

export interface ScoreRangeSettings {
  min: number;
  max: number;
  score_type: ScoreRangeType;
}

export interface EventDefinition {
  id?: string;
  created_at?: number;
  project_id: string;
  org_id: string;
  event_name: string;
  description: string;
  webhook?: string;
  webhook_headers?: Record<string, string> | null;
  detection_engine?: DetectionEngine;
  detection_scope: DetectionScope;
  keywords?: string;
  regex_pattern?: string;
  job_id?: string;
  score_range_settings?: ScoreRangeSettings;
}

export interface ABTest {
  version_id: string;
  score: number;
  score_std?: number;
  nb_tasks: number;
  first_task_timestamp: number;
  confidence_interval?: number[];
}

export interface SentimentThreshold {
  score: number;
  magnitude: number;
}

export interface ProjectSettings {
  events: Record<string, EventDefinition>;
  sentiment_threshold: SentimentThreshold;
}

export interface Project {
  id: string;
  created_at: number;
  project_name: string;
  org_id: string;
  settings?: ProjectSettings;
}

export interface HasEnoughLabelledTasks {
  project_id: string;
  enough_labelled_tasks: number;
  has_enough_labelled_tasks: boolean;
  currently_labelled_tasks: number;
}

export interface Test {
  id: string;
  project_id: string;
  created_by: string;
  created_at: number;
  last_updated_at: number;
  terminated_at?: number;
  status: string;
  summary?: Record<string, any>;
}

export interface Cluster {
  id: string;
  clustering_id: string;
  project_id: string;
  org_id: string;
  created_at: number;
  name: string;
  description: string;
  size: number;
  tasks_ids: string[];
}

export interface Clustering {
  id: string;
  clustering_id: string;
  project_id: string;
  org_id: string;
  created_at: number;
  type?: string;
  nb_clusters?: number;
  clusters_ids: string[];
  status?: "started" | "summaries" | "completed";
  clusters?: Cluster[] | null;
}

export interface CustomDateRange {
  from: Date | undefined;
  to: Date | undefined;
  created_at_start: number | undefined;
  created_at_end: number | undefined;
}

export interface MetadataFieldsToUniqueValues {
  [key: string]: string[];
}
export interface MetadataTypeToFieldsToUniqueValues {
  number: MetadataFieldsToUniqueValues;
  string: MetadataFieldsToUniqueValues;
}

export interface ProjectDataFilters {
  created_at_start?: number | null;
  created_at_end?: number | null;
  event_name?: string[] | null;
  flag?: string | null;
  metadata?: Record<string, any> | null;
  user_id?: string | null;
  last_eval_source?: string | null;
  sentiment?: string | null;
  language?: string | null;
  has_notes?: boolean | null;
  tasks_ids?: string[] | null;
  clustering_id?: string | null;
  clusters_ids?: string[] | null;
}
