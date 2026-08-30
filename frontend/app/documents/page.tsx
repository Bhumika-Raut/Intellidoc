"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, uploadDocument } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/components/Toast";
import type { DocumentRecord } from "@/types";

export default function DocumentsPage() {
  const { push } = useToast();
  const [docs, setDocs] = useState<DocumentRecord[]>([]);
  const [drag, setDrag] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    const list = await api.documents();
    setDocs(list);
  }, []);

  useEffect(() => {
    refresh().catch((e: Error) => push(e.message, "err"));
  }, [refresh, push]);

  useEffect(() => {
    const busy = docs.some((d) => d.status === "pending" || d.status === "processing");
    if (!busy) return;
    const t = setInterval(() => refresh().catch(() => undefined), 2000);
    return () => clearInterval(t);
  }, [docs, refresh]);

  async function onFiles(files: FileList | File[]) {
    for (const file of Array.from(files)) {
      try {
        setProgress(0);
        await uploadDocument(file, setProgress);
        push(`Uploaded ${file.name}`);
        await refresh();
      } catch (e) {
        push((e as Error).message, "err");
      } finally {
        setProgress(null);
      }
    }
  }

  async function remove(id: string) {
    if (!confirm("Delete this document and its embeddings?")) return;
    try {
      await api.deleteDocument(id);
      push("Document deleted");
      await refresh();
    } catch (e) {
      push((e as Error).message, "err");
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl">Documents</h1>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          PDF, DOCX, TXT, and Markdown. Files are extracted, chunked, and embedded locally.
        </p>
      </header>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          if (e.dataTransfer.files.length) void onFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 transition ${
          drag ? "border-moss-500 bg-moss-500/5" : "border-stone-300 bg-white dark:border-stone-700 dark:bg-ink-800"
        }`}
      >
        <input
          type="file"
          className="sr-only"
          accept=".pdf,.docx,.txt,.md"
          multiple
          onChange={(e) => e.target.files && void onFiles(e.target.files)}
        />
        <p className="font-medium">Drop files here or browse</p>
        <p className="mt-1 text-sm text-stone-500">Maximum size is configured on the server (default 15 MB).</p>
        {progress !== null && (
          <div className="mt-4 h-2 w-64 overflow-hidden rounded-full bg-stone-200">
            <div className="h-full bg-moss-500 transition-all" style={{ width: `${progress}%` }} />
          </div>
        )}
      </label>
      {docs.length === 0 ? (
        <EmptyState
          title="No documents yet"
          body="Upload the sample files from data/sample_documents to run the demo."
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white dark:border-stone-800 dark:bg-ink-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-stone-50 text-xs uppercase text-stone-500 dark:bg-ink-900">
              <tr>
                <th className="px-4 py-3 font-medium">Filename</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Size</th>
                <th className="px-4 py-3 font-medium">Uploaded</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Chunks</th>
                <th className="px-4 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className="border-t border-stone-100 dark:border-stone-800">
                  <td className="px-4 py-3">
                    <Link className="hover:underline" href={`/documents/${d.id}`}>
                      {d.original_filename}
                    </Link>
                  </td>
                  <td className="px-4 py-3 uppercase">{d.file_ext.replace(".", "")}</td>
                  <td className="px-4 py-3">{formatBytes(d.size_bytes)}</td>
                  <td className="px-4 py-3">{formatDate(d.created_at)}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={d.status} />
                  </td>
                  <td className="px-4 py-3">{d.chunk_count}</td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="text-red-600 hover:underline" onClick={() => void remove(d.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
