import axios from "axios";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: "application/json",
  },
});

export function apiUrl(path: string): string {
  if (!path) return path;
  if (/^https?:\/\//.test(path)) return path;
  if (path.startsWith("/api/v1/")) {
    return `${API_BASE_URL.replace(/\/api\/v1$/, "")}${path}`;
  }
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? "GET").toUpperCase();
  let data: unknown = init?.body;

  if (typeof data === "string") {
    try {
      data = JSON.parse(data);
    } catch {
      data = init?.body;
    }
  }

  try {
    const response = await apiClient.request<T>({
      url: path.startsWith("/") ? path : `/${path}`,
      method,
      headers: init?.headers as Record<string, string> | undefined,
      data,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail =
        (error.response?.data as { detail?: string } | undefined)?.detail ??
        `요청에 실패했습니다. (${error.response?.status ?? "네트워크 오류"})`;
      throw new Error(detail);
    }
    throw error;
  }
}
