export interface SsotDocSelectedTarget {
  section: string;
  path: string;
  label: string;
  kind: string;
}

export interface SsotDocSourceResponse {
  ok: boolean;
  ip: string;
  ssot_path: string;
  section: string;
  path: string;
  label: string;
  kind: string;
  value: unknown;
  yaml: string;
  feedback: Array<Record<string, unknown>>;
  error?: string;
}

export interface SsotDocFeedbackResponse {
  ok: boolean;
  ip?: string;
  section?: string;
  path?: string;
  field?: string;
  feedback_id?: string;
  feedback_count?: number;
  ssot_path?: string;
  doc_url?: string;
  error?: string;
}

export interface SsotDocSourceRequest {
  ip: string;
  target: SsotDocSelectedTarget | null;
}

export interface SsotDocFeedbackSubmitRequest {
  ip: string;
  target: SsotDocSelectedTarget | null;
  comment: string;
  value?: string;
  field?: string;
}

export interface SsotDocChatPrefillContext {
  ip: string;
  target: SsotDocSelectedTarget;
  comment: string;
  selectedText?: string;
  source?: SsotDocSourceResponse | null;
}

export interface SsotDocCommentEventDetail extends SsotDocChatPrefillContext {
  text: string;
}
