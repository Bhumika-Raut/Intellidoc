import { cn } from "@/lib/utils";
import type { DocumentStatus } from "@/types";

const labels: Record<DocumentStatus, string> = {
  pending: "Queued",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        status === "ready" && "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
        status === "processing" && "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
        status === "pending" && "bg-stone-200 text-stone-700 dark:bg-stone-800 dark:text-stone-200",
        status === "failed" && "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200"
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          status === "ready" && "bg-emerald-500",
          status === "processing" && "animate-pulse bg-amber-500",
          status === "pending" && "bg-stone-400",
          status === "failed" && "bg-red-500"
        )}
      />
      {labels[status]}
    </span>
  );
}
