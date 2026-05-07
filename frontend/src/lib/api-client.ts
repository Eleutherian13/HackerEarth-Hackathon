import { request } from "./api";

const normalizeLegacyPath = (path: string) => {
  if (path.startsWith("/api/v1")) {
    return path.slice("/api/v1".length) || "/";
  }
  return path;
};

const client = {
  get<T = unknown>(path: string, init: RequestInit = {}) {
    return request<T>(normalizeLegacyPath(path), { ...init, method: "GET" });
  },
  post<T = unknown>(path: string, body?: unknown, init: RequestInit = {}) {
    const headers = new Headers(init.headers ?? {});
    if (body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    return request<T>(normalizeLegacyPath(path), {
      ...init,
      method: "POST",
      headers,
      body: body === undefined ? init.body : typeof body === "string" ? body : JSON.stringify(body),
    });
  },
  put<T = unknown>(path: string, body?: unknown, init: RequestInit = {}) {
    const headers = new Headers(init.headers ?? {});
    if (body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    return request<T>(normalizeLegacyPath(path), {
      ...init,
      method: "PUT",
      headers,
      body: body === undefined ? init.body : typeof body === "string" ? body : JSON.stringify(body),
    });
  },
  delete<T = unknown>(path: string, init: RequestInit = {}) {
    return request<T>(normalizeLegacyPath(path), { ...init, method: "DELETE" });
  },
};

export default client;
