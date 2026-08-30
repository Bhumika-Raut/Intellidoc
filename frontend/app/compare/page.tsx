"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import type { CompareResponse, DocumentRecord } from "@/types";

export default function ComparePage() {
  const { push } = useToast();
  const [docs, setDocs] = useState<DocumentRecord[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .documents()
      .then((list) => {
        const ready = list.filter((d) => d.status === "ready");
        setDocs(ready);
        if (ready[0]) setA(ready[0].id);
        if (ready[1]) setB(ready[1].id);
      })
      .catch((e: Error) => push(e.message, "err"));
  }, [push]);

  async function run() {
    setBusy(true);
    try {
      setResult(await api.compare(a, b));
    } catch (e) {
      push((e as Error).message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl">Compare documents</h1>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          Retrieval-grounded comparison. Try Helios spec v1 vs v2 from the sample folder.
        </p>
      </header>
      <div className="grid gap-4 rounded-2xl border border-stone-200 bg-white p-5 md:grid-cols-2 dark:border-stone-800 dark:bg-ink-800">
        <label className="text-sm">
          Document A
          <select className="mt-1 w-full rounded-xl border px-3 py-2 dark:border-stone-700 dark:bg-ink-900" value={a} onChange={(e) => setA(e.target.value)}>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Document B
          <select className="mt-1 w-full rounded-xl border px-3 py-2 dark:border-stone-700 dark:bg-ink-900" value={b} onChange={(e) => setB(e.target.value)}>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename}
              </option>
            ))}
          </select>
        </label>
      </div>
      <button
        type="button"
        disabled={busy || !a || !b}
        onClick={() => void run()}
        className="rounded-xl bg-moss-500 px-5 py-2.5 text-sm text-white disabled:opacity-50"
      >
        {busy ? "Comparing…" : "Compare"}
      </button>
      {result && (
        <div className="space-y-4">
          <p className="text-sm text-stone-600 dark:text-stone-400">{result.summary}</p>
          <div className="overflow-hidden rounded-2xl border border-stone-200 dark:border-stone-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-stone-50 dark:bg-ink-800">
                <tr>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {result.sections.map((s) => (
                  <tr key={s.category} className="border-t border-stone-100 dark:border-stone-800">
                    <td className="px-4 py-3 align-top font-medium">{s.category}</td>
                    <td className="px-4 py-3">{s.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
