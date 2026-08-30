"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import type { ActionItem, DocumentRecord, InsightsResponse } from "@/types";

export default function InsightsPage() {
  const { push } = useToast();
  const [docs, setDocs] = useState<DocumentRecord[]>([]);
  const [id, setId] = useState("");
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [actions, setActions] = useState<ActionItem[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api
      .documents()
      .then((list) => {
        const ready = list.filter((d) => d.status === "ready");
        setDocs(ready);
        if (ready[0]) setId(ready[0].id);
      })
      .catch((e: Error) => push(e.message, "err"));
  }, [push]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl">Extract insights</h1>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          Structured extraction from retrieved context — people, dates, risks, and action items.
        </p>
      </header>
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Document
          <select className="mt-1 block min-w-64 rounded-xl border px-3 py-2 dark:border-stone-700 dark:bg-ink-800" value={id} onChange={(e) => setId(e.target.value)}>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!id || busy !== null}
          className="rounded-xl bg-moss-500 px-4 py-2 text-sm text-white disabled:opacity-50"
          onClick={async () => {
            setBusy("insights");
            try {
              setInsights(await api.insights(id));
            } catch (e) {
              push((e as Error).message, "err");
            } finally {
              setBusy(null);
            }
          }}
        >
          {busy === "insights" ? "Extracting…" : "Extract insights"}
        </button>
        <button
          type="button"
          disabled={!id || busy !== null}
          className="rounded-xl border px-4 py-2 text-sm dark:border-stone-600"
          onClick={async () => {
            setBusy("actions");
            try {
              setActions((await api.actionItems(id)).items);
            } catch (e) {
              push((e as Error).message, "err");
            } finally {
              setBusy(null);
            }
          }}
        >
          {busy === "actions" ? "Generating…" : "Generate action items"}
        </button>
      </div>
      {insights && (
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(insights).map(([k, items]) => (
            <section key={k} className="rounded-2xl border border-stone-200 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
              <h2 className="text-xs uppercase tracking-wide text-stone-500">{k.replaceAll("_", " ")}</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {items.length === 0 && <li className="text-stone-400">None found</li>}
                {items.map((it, i) => (
                  <li key={i} className="rounded-lg bg-stone-50 px-3 py-2 dark:bg-ink-900">
                    <p>{it.value}</p>
                    {it.source ? <p className="text-xs text-stone-500">{it.source}</p> : null}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
      {actions && (
        <div className="space-y-3">
          {actions.map((a, i) => (
            <article key={i} className="rounded-2xl border border-stone-200 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
              <p className="text-xs font-medium uppercase text-moss-500">{a.priority} priority</p>
              <h3 className="mt-1 font-medium">{a.task}</h3>
              <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">{a.description}</p>
              {a.deadline ? <p className="mt-2 text-sm">Deadline: {a.deadline}</p> : null}
              <p className="mt-2 text-xs text-stone-500">Source: {a.source}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
