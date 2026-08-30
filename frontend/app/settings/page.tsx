"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";

export default function SettingsPage() {
  const { push } = useToast();
  const [settings, setSettings] = useState<Record<string, string | number> | null>(null);

  useEffect(() => {
    api
      .publicSettings()
      .then(setSettings)
      .catch((e: Error) => push(e.message, "err"));
  }, [push]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl">Settings</h1>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          Runtime configuration from the backend. API keys are never sent to the browser.
        </p>
      </header>
      <div className="rounded-2xl border border-stone-200 bg-white p-5 dark:border-stone-800 dark:bg-ink-800">
        {!settings && <p className="text-sm text-stone-500">Loading…</p>}
        {settings && (
          <dl className="grid gap-4 sm:grid-cols-2">
            {Object.entries(settings).map(([k, v]) => (
              <div key={k}>
                <dt className="text-xs uppercase text-stone-500">{k.replaceAll("_", " ")}</dt>
                <dd className="mt-1 font-medium">{String(v)}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
      <section className="rounded-2xl border border-stone-200 bg-white p-5 text-sm dark:border-stone-800 dark:bg-ink-800">
        <h2 className="font-display text-lg">How to switch providers</h2>
        <p className="mt-2 text-stone-600 dark:text-stone-400">
          Edit <code className="rounded bg-stone-100 px-1 dark:bg-stone-900">.env</code> on the backend: set{" "}
          <code>LLM_PROVIDER</code> to <code>groq</code>, <code>openai</code>, or <code>mock</code>. Embeddings default to
          local <code>sentence-transformers</code> (<code>EMBEDDING_PROVIDER=local</code>).
        </p>
      </section>
    </div>
  );
}
