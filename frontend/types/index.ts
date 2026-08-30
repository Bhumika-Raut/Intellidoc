export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export type DocumentRecord = {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  file_ext: string;
  size_bytes: number;
  status: DocumentStatus;
  chunk_count: number;
  page_count: number;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type Citation = {
  document_id: string;
  filename: string;
  page: number | null;
  section: string | null;
  chunk_index: number | null;
  excerpt: string;
  score: number | null;
};

export type ChatResponse = {
  conversation_id: string;
  answer: string;
  citations: Citation[];
  unsupported: boolean;
};

export type SearchHit = {
  document_id: string;
  filename: string;
  page: number | null;
  section: string | null;
  excerpt: string;
  score: number | null;
};

export type SummaryResponse = {
  overview: string;
  key_points: string[];
  important_findings: string[];
  important_numbers: string[];
  risks: string[];
  recommendations: string[];
};

export type CompareResponse = {
  document_a: string;
  document_b: string;
  sections: { category: string; details: string }[];
  summary: string;
};

export type InsightItem = { value: string; source: string | null };

export type InsightsResponse = {
  people: InsightItem[];
  organizations: InsightItem[];
  dates: InsightItem[];
  amounts: InsightItem[];
  technologies: InsightItem[];
  requirements: InsightItem[];
  deadlines: InsightItem[];
  risks: InsightItem[];
  action_items: InsightItem[];
};

export type ActionItem = {
  task: string;
  description: string;
  priority: string;
  deadline: string | null;
  source: string;
};

export type DashboardStats = {
  documents: number;
  total_chunks: number;
  questions_asked: number;
  ai_summaries: number;
  recent_documents: DocumentRecord[];
  recent_questions: { id: string; query: string; created_at: string }[];
  knowledge_base: DocumentRecord[];
};

export type Conversation = {
  id: string;
  title: string;
  created_at: string | null;
  messages: {
    id: string;
    role: string;
    content: string;
    citations: Citation[];
    created_at: string | null;
  }[];
};
