"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/EmptyState";
import type { DashboardStats } from "@/types";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-100">
        Could not reach the API. Start the backend on port 8000. {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="grid gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }

  const cards = [
    { label: "Documents", value: data.documents },
    { label: "Total chunks", value: data.total_chunks },
    { label: "Questions asked", value: data.questions_asked },
    { label: "AI summaries", value: data.ai_summaries },
  ];

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-3xl">Overview</h1>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          Knowledge base health for your uploaded documents.
        </p>
      </header>
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-card dark:border-stone-800 dark:bg-ink-800">
            <p className="text-xs uppercase tracking-wide text-stone-500">{c.label}</p>
            <p className="mt-2 font-display text-3xl">{c.value}</p>
          </div>
        ))}
      </section>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-stone-200/80 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
          <h2 className="font-display text-lg">Recent documents</h2>
          <ul className="mt-4 space-y-3">
            {data.recent_documents.length === 0 && (
              <li className="text-sm text-stone-500">No documents yet. Upload from Documents.</li>
            )}
            {data.recent_documents.map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-3 text-sm">
                <Link href={`/documents/${d.id}`} className="truncate hover:underline">
                  {d.original_filename}
                </Link>
                <StatusBadge status={d.status} />
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-2xl border border-stone-200/80 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
          <h2 className="font-display text-lg">Recent questions</h2>
          <ul className="mt-4 space-y-3">
            {data.recent_questions.length === 0 && (
              <li className="text-sm text-stone-500">No questions yet. Open Chat to ask one.</li>
            )}
            {data.recent_questions.map((q) => (
              <li key={q.id} className="text-sm">
                <p className="text-ink-900 dark:text-ink-50">{q.query}</p>
                <p className="text-xs text-stone-500">{formatDate(q.created_at)}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
      <section className="rounded-2xl border border-stone-200/80 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
        <h2 className="font-display text-lg">Knowledge base</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-stone-500">
              <tr>
                <th className="pb-2 font-medium">Document</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Chunks</th>
              </tr>
            </thead>
            <tbody>
              {data.knowledge_base.map((d) => (
                <tr key={d.id} className="border-t border-stone-100 dark:border-stone-800">
                  <td className="py-2">{d.original_filename}</td>
                  <td>
                    <StatusBadge status={d.status} />
                  </td>
                  <td>{d.chunk_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
