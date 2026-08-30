"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { EmptyState } from "@/components/EmptyState";
import type { SearchHit } from "@/types";

export default function SearchPage() {
  const { push } = useToast();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    try {
      setHits(await api.search(query));
    } catch (e) {
      push((e as Error).message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl">Semantic search</h1>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          Find passages across the knowledge base. Example: “Find all references to database migration.”
        </p>
      </header>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <input
          className="flex-1 rounded-xl border px-4 py-3 text-sm dark:border-stone-700 dark:bg-ink-800"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What documents mention authentication?"
          aria-label="Search query"
        />
        <button type="submit" disabled={busy || !query.trim()} className="rounded-xl bg-moss-500 px-5 py-3 text-sm text-white disabled:opacity-50">
          {busy ? "Searching…" : "Search"}
        </button>
      </form>
      {hits && hits.length === 0 && (
        <EmptyState title="No matching passages" body="Try different wording, or upload more documents." />
      )}
      {hits && hits.length > 0 && (
        <ul className="space-y-3">
          {hits.map((h, i) => (
            <li key={i} className="rounded-2xl border border-stone-200 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
              <p className="text-sm font-medium">
                {h.filename}
                {h.page != null ? ` · page ${h.page}` : ""}
                {h.section ? ` · ${h.section}` : ""}
                {h.score != null ? ` · relevance ${h.score}` : ""}
              </p>
              <p className="mt-2 text-sm text-stone-600 dark:text-stone-400">{h.excerpt}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
