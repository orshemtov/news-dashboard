import type { MediaAttachment } from '@/types';

/**
 * Build a full URL for a media attachment served by the backend.
 * Attachment URLs are relative paths — we prefix them with the API base URL.
 */
export function mediaUrl(relativePath: string): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';
  // If baseUrl is a full URL (like http://10.0.0.1:8000/api),
  // we need to make sure we don't end up with /api/api/media
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${cleanBase}/media/${relativePath}`;
}

/**
 * Get the display URL for a media attachment.
 * Always returns the full-resolution image (thumbnails are too low-res).
 */
export function thumbnailUrl(attachment: MediaAttachment): string {
  if (attachment.type === 'photo') {
    return mediaUrl(attachment.url);
  }
  // For videos, try thumbnail_url (legacy), otherwise empty
  if (attachment.thumbnail_url) {
    return mediaUrl(attachment.thumbnail_url);
  }
  return '';
}

/**
 * Format a file size in bytes to a human-readable string.
 */
export function formatFileSize(bytes: number | null): string {
  if (bytes == null || bytes === 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Format a duration in seconds to mm:ss.
 */
export function formatDuration(seconds: number | null): string {
  if (seconds == null || seconds === 0) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}
