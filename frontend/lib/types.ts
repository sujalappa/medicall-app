export interface Call {
  id: string;
  filename: string;
  language: string;
  created_at: string;
}

export interface TranscriptSegment {
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
}

export interface Symptom {
  text: string;
  timestamp?: number;
  speaker?: string;
  severity?: string;
  duration?: string;
}

export interface Prescription {
  text: string;
  timestamp?: number;
  speaker?: string;
}

export interface FollowUp {
  text: string;
  timestamp?: number;
  speaker?: string;
}

export interface SOAPNote {
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
}

export interface Insights {
  symptoms?: Symptom[];
  prescriptions?: Prescription[];
  follow_ups?: FollowUp[];
  soap_note?: SOAPNote;
  patient_sentiment?: SentimentPoint[];
}

export interface SentimentPoint {
  timestamp: number;
  score: number;
  label: string;
  speaker: string;
}

export interface QAResponse {
  answer: string;
  sources?: string[];
}

export type ConnectionStatus = "connecting" | "connected" | "reconnecting" | "closed";

export interface StreamEvent {
  type: string;
  seq?: number;
  status?: string;
  progress?: number;
  is_partial?: boolean;
  segment?: TranscriptSegment;
}
