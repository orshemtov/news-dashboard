// ---------------------------------------------------------------------------
// Article
// ---------------------------------------------------------------------------

export interface Article {
  id: string;
  title: string | null;
  content: string;
  url: string | null;
  author: string | null;
  language: string | null;
  source_type: string;
  source_name: string;
  published_at: string;
  summary: string | null;
  ingested_at: string;
  is_duplicate: boolean;
  dedup_cluster_id: string | null;
  metadata_: Record<string, unknown>;
}

export interface ArticleDetail extends Article {
  raw_data: Record<string, unknown>;
  embedding: number[] | null;
}

export interface ArticleListResponse {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Source
// ---------------------------------------------------------------------------

export interface Source {
  id: string;
  name: string;
  source_type: string;
  config: Record<string, unknown>;
  poll_interval_seconds: number;
  enabled: boolean;
  last_polled_at: string | null;
  article_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceCreate {
  name: string;
  source_type: string;
  config?: Record<string, unknown>;
  poll_interval_seconds?: number;
  enabled?: boolean;
}

export interface SourceUpdate {
  name?: string;
  config?: Record<string, unknown>;
  poll_interval_seconds?: number;
  enabled?: boolean;
}

export interface SourcePreset {
  name: string;
  source_type: string;
  config: Record<string, unknown>;
  category: string;
  description: string;
}

export interface SourceTestRequest {
  source_type: string;
  config: Record<string, unknown>;
}

export interface SourceTestResponse {
  success: boolean;
  message: string;
  sample_items: Record<string, unknown>[];
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export interface SearchRequest {
  query: string;
  mode?: 'keyword' | 'semantic' | 'hybrid';
  sources?: string[];
  source_types?: string[];
  language?: string;
  from_date?: string;
  to_date?: string;
  include_duplicates?: boolean;
  page?: number;
  page_size?: number;
}

export interface SearchResponse {
  items: Article[];
  total: number;
  query: string;
  mode: string;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export interface ChatMessageRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  cited_article_ids: string[];
  model_used: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ConversationListResponse {
  items: Conversation[];
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export interface ArticlesByHour {
  hour: string;
  count: number;
}

export interface DashboardStats {
  total_articles: number;
  articles_today: number;
  active_sources: number;
  total_sources: number;
  articles_by_source: Record<string, number>;
  articles_by_hour: ArticlesByHour[];
  languages: Record<string, number>;
  latest_ingestion: string | null;
}

// ---------------------------------------------------------------------------
// AI
// ---------------------------------------------------------------------------

export interface SummarizeResponse {
  article_id: string;
  title: string | null;
  summary: string;
  status: string;
}

export interface TranslateResponse {
  article_id: string;
  title: string | null;
  target_language: string;
  translated_content: string;
  status: string;
}
