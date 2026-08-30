"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/EmptyState";
import { useToast } from "@/components/Toast";
import type { ActionItem, DocumentRecord, InsightsResponse, SummaryResponse } from "@/types";

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { push } = useToast();
  const [doc, setDoc] = useState<DocumentRecord | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [actions, setActions] = useState<ActionItem[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api.document(id).then(setDoc).catch((e: Error) => push(e.message, "err"));
  }, [id, push]);

  async function run<T>(label: string, fn: () => Promise<T>, apply: (v: T) => void) {
    setBusy(label);
    try {
      apply(await fn());
    } catch (e) {
      push((e as Error).message, "err");
    } finally {
      setBusy(null);
    }
  }

  if (!doc) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/documents" className="text-sm text-moss-500 hover:underline">
          ← Documents
        </Link>
        <h1 className="mt-2 font-display text-3xl">{doc.original_filename}</h1>
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusBadge status={doc.status} />
        </div>
      </div>
      <dl className="grid gap-4 rounded-2xl border border-stone-200 bg-white p-5 text-sm sm:grid-cols-2 dark:border-stone-800 dark:bg-ink-800">
        <Item label="Type" value={doc.file_ext.toUpperCase()} />
        <Item label="Size" value={formatBytes(doc.size_bytes)} />
        <Item label="Uploaded" value={formatDate(doc.created_at)} />
        <Item label="Chunks" value={String(doc.chunk_count)} />
        <Item label="Pages / sections" value={String(doc.page_count)} />
        <Item label="MIME" value={doc.content_type} />
        {doc.error_message ? <Item label="Error" value={doc.error_message} /> : null}
      </dl>
      <div className="flex flex-wrap gap-3">
        <button
          className="rounded-xl bg-moss-500 px-4 py-2 text-sm text-white disabled:opacity-50"
          disabled={busy !== null || doc.status !== "ready"}
          onClick={() => void run("summary", () => api.summarize(id), setSummary)}
        >
          {busy === "summary" ? "Summarizing…" : "Executive summary"}
        </button>
        <button
          className="rounded-xl border border-stone-300 px-4 py-2 text-sm dark:border-stone-600"
          disabled={busy !== null || doc.status !== "ready"}
          onClick={() => void run("insights", () => api.insights(id), setInsights)}
        >
          {busy === "insights" ? "Extracting…" : "Extract insights"}
        </button>
        <button
          className="rounded-xl border border-stone-300 px-4 py-2 text-sm dark:border-stone-600"
          disabled={busy !== null || doc.status !== "ready"}
          onClick={() =>
            void run("actions", () => api.actionItems(id), (r) => setActions(r.items))
          }
        >
          {busy === "actions" ? "Generating…" : "Action items"}
        </button>
        <Link href={`/chat?doc=${id}`} className="rounded-xl border border-stone-300 px-4 py-2 text-sm dark:border-stone-600">
          Ask about this file
        </Link>
      </div>
      {summary && (
        <section className="space-y-4 rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-800 dark:bg-ink-800">
          <h2 className="font-display text-xl">Executive summary</h2>
          <p>{summary.overview}</p>
          <List title="Key points" items={summary.key_points} />
          <List title="Important findings" items={summary.important_findings} />
          <List title="Important numbers" items={summary.important_numbers} />
          <List title="Risks" items={summary.risks} />
          <List title="Recommendations" items={summary.recommendations} />
        </section>
      )}
      {insights && (
        <section className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-800 dark:bg-ink-800">
          <h2 className="font-display text-xl">Insights</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {Object.entries(insights).map(([k, items]) => (
              <div key={k}>
                <h3 className="text-xs uppercase tracking-wide text-stone-500">{k.replace("_", " ")}</h3>
                <ul className="mt-2 space-y-1 text-sm">
                  {items.length === 0 && <li className="text-stone-400">None found</li>}
                  {items.map((it, i) => (
                    <li key={i}>
                      {it.value}
                      {it.source ? <span className="block text-xs text-stone-500">{it.source}</span> : null}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}
      {actions && (
        <section className="space-y-3">
          <h2 className="font-display text-xl">Action items</h2>
          {actions.length === 0 && <p className="text-sm text-stone-500">No action items in the retrieved context.</p>}
          {actions.map((a, i) => (
            <article key={i} className="rounded-2xl border border-stone-200 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
              <p className="text-xs font-medium uppercase text-moss-500">{a.priority} priority</p>
              <h3 className="mt-1 font-medium">{a.task}</h3>
              <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">{a.description}</p>
              {a.deadline ? <p className="mt-2 text-sm">Deadline: {a.deadline}</p> : null}
              <p className="mt-2 text-xs text-stone-500">Source: {a.source}</p>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}

function Item({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase text-stone-500">{label}</dt>
      <dd className="mt-1">{value}</dd>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-medium">{title}</h3>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
        {items.length === 0 && <li className="text-stone-400">Not found in the document.</li>}
        {items.map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
    </div>
  );
}
