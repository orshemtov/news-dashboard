import axios from 'axios';
import type {
  ArticleDetail,
  ArticleListResponse,
  ChatMessage,
  ChatMessageRequest,
  Conversation,
  ConversationListResponse,
  DashboardStats,
  SearchRequest,
  SearchResponse,
  Source,
  SourceCreate,
  SourcePreset,
  SourceTestRequest,
  SourceTestResponse,
  SourceUpdate,
  SummarizeResponse,
  TranslateResponse,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Articles
// ---------------------------------------------------------------------------

export interface ArticleListParams {
  page?: number;
  page_size?: number;
  source_type?: string;
  source_name?: string;
  language?: string;
  is_duplicate?: boolean;
  from_date?: string;
  to_date?: string;
}

export const getArticles = (params?: ArticleListParams) =>
  api.get<ArticleListResponse>('/articles', { params }).then((r) => r.data);

export const getArticle = (id: string) =>
  api.get<ArticleDetail>(`/articles/${id}`).then((r) => r.data);

export const deleteArticle = (id: string) =>
  api.delete<void>(`/articles/${id}`);

// ---------------------------------------------------------------------------
// Sources
// ---------------------------------------------------------------------------

export const getSources = () =>
  api.get<Source[]>('/sources').then((r) => r.data);

export const createSource = (data: SourceCreate) =>
  api.post<Source>('/sources', data).then((r) => r.data);

export const updateSource = (id: string, data: SourceUpdate) =>
  api.patch<Source>(`/sources/${id}`, data).then((r) => r.data);

export const deleteSource = (id: string) =>
  api.delete<void>(`/sources/${id}`);

export const testSource = (data: SourceTestRequest) =>
  api.post<SourceTestResponse>('/sources/test', data).then((r) => r.data);

export const getSourcePresets = () =>
  api.get<SourcePreset[]>('/sources/presets').then((r) => r.data);

export const searchTelegramChannels = (query: string) =>
  api.get<{ message: string }>('/sources/telegram/search', { params: { query } }).then((r) => r.data);

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export const searchArticles = (data: SearchRequest) =>
  api.post<SearchResponse>('/search', data).then((r) => r.data);

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export const getStats = () =>
  api.get<DashboardStats>('/stats').then((r) => r.data);

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export const sendChatMessage = (data: ChatMessageRequest) =>
  api.post<ChatMessage>('/chat', data).then((r) => r.data);

export const getConversations = () =>
  api.get<ConversationListResponse>('/chat/conversations').then((r) => r.data);

export const getConversation = (id: string) =>
  api.get<Conversation>(`/chat/conversations/${id}`).then((r) => r.data);

export const deleteConversation = (id: string) =>
  api.delete<void>(`/chat/conversations/${id}`);

// ---------------------------------------------------------------------------
// AI
// ---------------------------------------------------------------------------

export const summarizeArticle = (id: string) =>
  api.post<SummarizeResponse>(`/ai/summarize/${id}`).then((r) => r.data);

export const translateArticle = (id: string, target_language: string) =>
  api.post<TranslateResponse>(`/ai/translate/${id}`, null, { params: { target_language } }).then((r) => r.data);

export default api;
