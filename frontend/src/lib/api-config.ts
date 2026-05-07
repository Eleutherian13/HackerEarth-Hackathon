// FastAPI backend base URL.
// Override via VITE_API_URL in your local environment (e.g. .env.local).
export const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api/v1";
