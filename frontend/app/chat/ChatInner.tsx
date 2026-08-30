"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, API_BASE } from "@/lib/api";
import { useToast } from "@/components/Toast";
import type { Citation, Conversation } from "@/types";

type Turn = { role: "user" | "assistant"; content: string; citations: Citation[] };

export default function ChatInner() {
  const { push } = useToast();
  const params = useSearchParams();
  const docFilter = params.get("doc");
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .history()
      .then((convos: Conversation[]) => {
        const first = convos[0];
        if (!first) return;
        setConversationId(first.id);
        setTurns(
          first.messages.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
            citations: m.citations || [],
          }))
        );
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, loading]);

  async function send(text?: string) {
    const q = (text ?? question).trim();
    if (!q || loading) return;
    setQuestion("");
    setTurns((t) => [...t, { role: "user", content: q, citations: [] }]);
    setLoading(true);
    try {
      const streamed = await streamChat(q, conversationId, docFilter ? [docFilter] : undefined);
      if (streamed && streamed.answer) {
        setConversationId(streamed.conversationId);
        setTurns((t) => [
          ...t,
          { role: "assistant", content: streamed.answer, citations: streamed.citations },
        ]);
      } else {
        const res = await api.chat(q, conversationId, docFilter ? [docFilter] : undefined);
        setConversationId(res.conversation_id);
        setTurns((t) => [...t, { role: "assistant", content: res.answer, citations: res.citations }]);
      }
    } catch (e) {
      push((e as Error).message, "err");
      setTurns((t) => t.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }

  const lastAssistant = [...turns].reverse().find((t) => t.role === "assistant");

  async function copyLast() {
    if (!lastAssistant) return;
    await navigator.clipboard.writeText(lastAssistant.content);
    push("Answer copied");
  }

  async function regenerate() {
    const lastUser = [...turns].reverse().find((t) => t.role === "user");
    if (!lastUser) return;
    setTurns((t) => {
      const copy = [...t];
      if (copy[copy.length - 1]?.role === "assistant") copy.pop();
      if (copy[copy.length - 1]?.role === "user") copy.pop();
      return copy;
    });
    await send(lastUser.content);
  }

  async function clearAll() {
    if (conversationId) {
      try {
        await api.clearConversation(conversationId);
      } catch {
        /* still clear local */
      }
    }
    setTurns([]);
    setConversationId(null);
  }

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col">
      <header className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl">Chat</h1>
          <p className="text-sm text-stone-600 dark:text-stone-400">
            Answers use retrieved chunks only. {docFilter ? "Scoped to one document." : "Searching the full knowledge base."}
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" className="rounded-lg border px-3 py-1.5 text-sm dark:border-stone-600" onClick={() => void copyLast()}>
            Copy
          </button>
          <button type="button" className="rounded-lg border px-3 py-1.5 text-sm dark:border-stone-600" onClick={() => void regenerate()}>
            Regenerate
          </button>
          <button type="button" className="rounded-lg border px-3 py-1.5 text-sm dark:border-stone-600" onClick={() => void clearAll()}>
            Clear
          </button>
        </div>
      </header>
      <div className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-stone-200 bg-white p-4 dark:border-stone-800 dark:bg-ink-800">
        {turns.length === 0 && (
          <p className="text-sm text-stone-500">Try: “What authentication mechanism does the product use?”</p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className={turn.role === "user" ? "ml-8" : "mr-8"}>
            <p className="text-xs uppercase tracking-wide text-stone-500">{turn.role}</p>
            <div className="mt-1 whitespace-pre-wrap rounded-xl bg-stone-50 px-4 py-3 text-sm dark:bg-ink-900">{turn.content}</div>
            {turn.citations.length > 0 && (
              <div className="mt-2">
                <button
                  type="button"
                  className="text-xs text-moss-500 hover:underline"
                  onClick={() => setExpanded(expanded === i ? null : i)}
                >
                  {expanded === i ? "Hide sources" : `Sources (${turn.citations.length})`}
                </button>
                {expanded === i && (
                  <ul className="mt-2 space-y-2">
                    {turn.citations.map((c, j) => (
                      <li key={j} className="rounded-lg border border-stone-200 p-3 text-xs dark:border-stone-700">
                        <p className="font-medium">
                          {c.filename}
                          {c.page != null ? ` · page ${c.page}` : ""}
                          {c.section ? ` · ${c.section}` : ""}
                          {c.score != null ? ` · score ${c.score}` : ""}
                        </p>
                        <p className="mt-1 text-stone-600 dark:text-stone-400">{c.excerpt}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ))}
        {loading && <p className="animate-pulse text-sm text-stone-500">Retrieving context and writing…</p>}
        <div ref={bottom} />
      </div>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          className="flex-1 rounded-xl border border-stone-300 bg-white px-4 py-3 text-sm dark:border-stone-700 dark:bg-ink-800"
          placeholder="Ask a question about your documents"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          aria-label="Question"
        />
        <button type="submit" disabled={loading || !question.trim()} className="rounded-xl bg-moss-500 px-5 py-3 text-sm text-white disabled:opacity-50">
          Send
        </button>
      </form>
    </div>
  );
}

async function streamChat(
  question: string,
  conversationId: string | null,
  documentIds?: string[]
): Promise<{ answer: string; citations: Citation[]; conversationId: string } | null> {
  try {
    const res = await fetch(`${API_BASE}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, conversation_id: conversationId, document_ids: documentIds }),
    });
    if (!res.ok || !res.body) return null;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let answer = "";
    let citations: Citation[] = [];
    let conv = conversationId || "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";
      for (const part of parts) {
        const line = part.replace(/^data: /, "").trim();
        if (!line) continue;
        const evt = JSON.parse(line) as {
          type: string;
          token?: string;
          citations?: Citation[];
          conversation_id?: string;
        };
        if (evt.type === "token" && evt.token) answer += evt.token;
        if (evt.type === "citations" && evt.citations) citations = evt.citations;
        if (evt.type === "done" && evt.conversation_id) conv = evt.conversation_id;
      }
    }
    return { answer, citations, conversationId: conv };
  } catch {
    return null;
  }
}
