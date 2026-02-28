// ---------------------------------------------------------------------------
// Text utilities for cleaning Telegram content and detecting RTL
// ---------------------------------------------------------------------------

/**
 * Hebrew Unicode range: \u0590-\u05FF (letters, points, cantillation marks)
 * Arabic Unicode range: \u0600-\u06FF
 */
const RTL_CHAR_RE = /[\u0590-\u05FF\u0600-\u06FF\uFB1D-\uFDFF\uFE70-\uFEFF]/;
const RTL_CHAR_COUNT_RE =
  /[\u0590-\u05FF\u0600-\u06FF\uFB1D-\uFDFF\uFE70-\uFEFF]/g;

/**
 * Detect if text is RTL based on actual content characters.
 * Falls back to language field if available.
 */
export function isRtl(
  text: string,
  language?: string | null,
): boolean {
  // If language is explicitly set, use it
  if (language) {
    const base = language.split('-')[0].toLowerCase();
    if (['he', 'ar', 'fa', 'ur'].includes(base)) return true;
    if (['en', 'fr', 'de', 'es', 'ru'].includes(base)) return false;
  }

  // Content-based detection: count RTL characters
  const rtlMatches = text.match(RTL_CHAR_COUNT_RE);
  if (!rtlMatches) return false;

  // If more than 30% of alphabetic characters are RTL, treat as RTL
  const alphaChars = text.replace(/[^a-zA-Z\u0590-\u05FF\u0600-\u06FF\uFB1D-\uFDFF\uFE70-\uFEFF]/g, '');
  if (alphaChars.length === 0) return false;

  return rtlMatches.length / alphaChars.length > 0.3;
}

/**
 * Quick check if a string starts with RTL content.
 */
export function startsWithRtl(text: string): boolean {
  // Find first alphabetic character and check if it's RTL
  for (const ch of text) {
    if (RTL_CHAR_RE.test(ch)) return true;
    if (/[a-zA-Z]/.test(ch)) return false;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Content cleaning
// ---------------------------------------------------------------------------

/**
 * Clean Telegram message content for display.
 *
 * Removes:
 * - Empty markdown links: `[ ](url)`
 * - Markdown link syntax: `[text](url)` → keeps text
 * - Markdown bold/italic: `**text**` / `__text__` → keeps text
 * - Inline URLs (bare https://... links)
 * - Common Telegram navigation prompts (Hebrew)
 * - Excessive whitespace
 */
export function cleanContent(raw: string): string {
  let text = raw;

  // 1. Remove empty/whitespace-only markdown links: [ ](url)
  text = text.replace(/\[\s*\]\([^)]*\)/g, '');

  // 2. Convert markdown links to just the text: [visible text](url) → visible text
  text = text.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1');

  // 3. Remove markdown bold: **text** → text
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');

  // 4. Remove markdown italic: __text__ → text
  text = text.replace(/__([^_]+)__/g, '$1');

  // 5. Remove remaining markdown emphasis: *text* → text (single asterisk)
  text = text.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '$1');

  // 6. Remove bare URLs (https://... or http://...)
  text = text.replace(/https?:\/\/\S+/g, '');

  // 7. Remove common Telegram navigation/promo lines (Hebrew)
  // "לקריאה נוחה במחשב" / "לקריאת נוחה בנייד" / "הצטרפו לערוץ" etc.
  text = text.replace(/[👈🏽👉🏽⬇️⬆️➡️⬅️🔗📢📌]+/g, '');
  text = text.replace(/לקריאה?\s+נוחה?\s+(במחשב|בנייד)/g, '');
  text = text.replace(/הצטרפו\s+ל(ערוץ|קבוצה)/g, '');

  // 8. Clean up excessive whitespace
  text = text.replace(/\n{3,}/g, '\n\n');
  text = text.replace(/[ \t]+/g, ' ');
  text = text.trim();

  return text;
}

/**
 * Get a clean display title from an article.
 * If no title, extracts first meaningful line from content.
 */
export function getDisplayTitle(
  title: string | null,
  content: string,
  maxLength = 120,
): string {
  if (title) return title;

  const cleaned = cleanContent(content);
  // Take first line or first `maxLength` chars
  const firstLine = cleaned.split('\n')[0].trim();
  if (firstLine.length <= maxLength) return firstLine;
  return firstLine.slice(0, maxLength) + '...';
}

/**
 * Get clean display content (body text after title).
 * When excludeTitle is provided, strips that text from the beginning.
 */
export function getDisplayContent(
  content: string,
  maxLength?: number,
  excludeTitle?: string,
): string {
  let cleaned = cleanContent(content);

  // Strip the title line from the beginning so we only show the rest
  if (excludeTitle) {
    const lines = cleaned.split('\n');
    const firstLine = lines[0].trim();
    if (firstLine === excludeTitle.trim()) {
      cleaned = lines.slice(1).join('\n').trim();
    }
  }

  if (!cleaned) return '';
  if (!maxLength) return cleaned;
  if (cleaned.length <= maxLength) return cleaned;
  return cleaned.slice(0, maxLength) + '...';
}
