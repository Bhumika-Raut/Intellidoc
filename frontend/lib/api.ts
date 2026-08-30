import { apiError } from "./utils";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {}),
    },
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(apiError(data, `Request failed (${res.status})`));
  return data as T;
}

export const api = {
  health: () => request<{ status: string; llm_provider: string }>("/api/health"),
  publicSettings: () => request<Record<string, string | number>>("/api/settings/public"),
  dashboard: () => request<import("@/types").DashboardStats>("/api/dashboard"),
  documents: () => request<import("@/types").DocumentRecord[]>("/api/documents"),
  document: (id: string) => request<import("@/types").DocumentRecord>(`/api/documents/${id}`),
  deleteDocument: (id: string) => request<void>(`/api/documents/${id}`, { method: "DELETE" }),
  processDocument: (id: string) =>
    request<import("@/types").DocumentRecord>(`/api/documents/${id}/process`, { method: "POST" }),
  summarize: (id: string) =>
    request<import("@/types").SummaryResponse>(`/api/documents/${id}/summarize`, { method: "POST" }),
  insights: (id: string) =>
    request<import("@/types").InsightsResponse>(`/api/documents/${id}/extract-insights`, {
      method: "POST",
    }),
  actionItems: (id: string) =>
    request<{ items: import("@/types").ActionItem[] }>(`/api/documents/${id}/action-items`, {
      method: "POST",
    }),
  compare: (a: string, b: string) =>
    request<import("@/types").CompareResponse>("/api/documents/compare", {
      method: "POST",
      body: JSON.stringify({ document_id_a: a, document_id_b: b }),
    }),
  search: (query: string) =>
    request<import("@/types").SearchHit[]>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
  chat: (question: string, conversation_id?: string | null, document_ids?: string[]) =>
    request<import("@/types").ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question, conversation_id, document_ids }),
    }),
  history: () => request<import("@/types").Conversation[]>("/api/chat/history"),
  clearConversation: (id: string) => request<void>(`/api/chat/${id}`, { method: "DELETE" }),
};

export function uploadDocument(
  file: File,
  onProgress: (pct: number) => void
): Promise<import("@/types").DocumentRecord> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}/api/documents/upload`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText || "{}");
        if (xhr.status >= 200 && xhr.status < 300) resolve(data);
        else reject(new Error(apiError(data, "Upload failed")));
      } catch {
        reject(new Error("Upload failed"));
      }
    };
    xhr.onerror = () => reject(new Error("Network error while uploading. Is the API running?"));
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export { BASE as API_BASE };
