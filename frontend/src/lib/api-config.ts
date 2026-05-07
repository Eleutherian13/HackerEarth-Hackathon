// FastAPI backend base URL.
// Override via VITE_API_URL in your local environment (e.g. .env.local).
// Supports values like:
// - http://localhost:8000
// - http://localhost:8000/api
// - http://localhost:8000/api/v1
const DEFAULT_API_ORIGIN = "http://localhost:8000";
const API_PREFIX = "/api/v1";

const normalizeApiBaseUrl = (raw: string | undefined): string => {
  const trimmed = (raw ?? "").trim();
  const base = (trimmed || `${DEFAULT_API_ORIGIN}${API_PREFIX}`).replace(
    /\/+$/,
    "",
  );

  if (/\/api\/v\d+$/i.test(base)) return base;
  if (/\/api$/i.test(base)) return `${base}/v1`;
  return `${base}${API_PREFIX}`;
};

export const API_BASE_URL = normalizeApiBaseUrl(
  import.meta.env.VITE_API_URL as string | undefined,
);
