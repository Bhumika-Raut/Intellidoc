export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-stone-300 bg-white/50 px-6 py-16 text-center dark:border-stone-700 dark:bg-ink-800/40">
      <p className="font-display text-xl text-ink-900 dark:text-ink-50">{title}</p>
      <p className="mt-2 max-w-md text-sm text-stone-600 dark:text-stone-400">{body}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-stone-200/80 dark:bg-stone-800 ${className}`} />;
}
