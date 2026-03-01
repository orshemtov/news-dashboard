import axios from 'axios';
import type {
  ArticleDetail,
  ArticleListResponse,
  ChannelSuggestion,
  DashboardStats,
  FacetsResponse,
  SearchRequest,
  SearchResponse,
  Source,
  SourceCreate,
  SourcePreset,
  SourceTestRequest,
  SourceTestResponse,
  SourceUpdate,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  // FastAPI expects repeated query params for arrays: ?key=v1&key=v2
  paramsSerializer: {
    indexes: null,
  },
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
  // Facet-style filters
  sources_include?: string[];
  sources_exclude?: string[];
  languages_include?: string[];
  languages_exclude?: string[];
  forwarded?: boolean;
  exclude_keywords?: string[];
}

export const getArticles = (params?: ArticleListParams) =>
  api.get<ArticleListResponse>('/articles', { params }).then((r) => r.data);

export const getFacets = (params?: Omit<ArticleListParams, 'page' | 'page_size'>) =>
  api.get<FacetsResponse>('/articles/facets', { params }).then((r) => r.data);

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

export const ingestSource = (id: string) =>
  api.post<{ source: string; new_articles: number }>(`/sources/${id}/ingest`).then((r) => r.data);

export interface TelegramChannelResult {
  id: number | null;
  title: string | null;
  username: string | null;
  participants_count: number | null;
}

export const searchTelegramChannels = (query: string) =>
  api.get<TelegramChannelResult[]>('/sources/telegram/search', { params: { query } }).then((r) => r.data);

export const getChannelSuggestions = (topK?: number) =>
  api.get<ChannelSuggestion[]>('/sources/suggestions', { params: topK ? { top_k: topK } : {} }).then((r) => r.data);

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

export default api;
