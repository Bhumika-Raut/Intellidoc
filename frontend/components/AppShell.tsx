"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import {
  FileText,
  LayoutDashboard,
  MessageSquare,
  Search,
  GitCompare,
  Sparkles,
  Settings,
  Moon,
  Sun,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/search", label: "Search", icon: Search },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/insights", label: "Insights", icon: Sparkles },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen bg-ink-50 text-ink-900 dark:bg-ink-900 dark:text-ink-50">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(15,107,92,0.08),_transparent_45%)] dark:bg-[radial-gradient(ellipse_at_top_right,_rgba(93,202,169,0.08),_transparent_40%)]" />
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-stone-200/80 bg-white/80 px-4 py-6 backdrop-blur-md dark:border-stone-800 dark:bg-ink-900/80 lg:flex">
        <Link href="/dashboard" className="mb-8 px-2">
          <p className="font-display text-2xl tracking-tight">IntelliDocs</p>
          <p className="text-xs text-stone-500">Knowledge & decision assistant</p>
        </Link>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition",
                  active
                    ? "bg-moss-500 text-white shadow-sm"
                    : "text-stone-600 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                )}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          type="button"
          aria-label="Toggle color theme"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="mt-4 flex items-center gap-2 rounded-xl border border-stone-200 px-3 py-2 text-sm dark:border-stone-700"
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
      </aside>
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-stone-200/70 bg-ink-50/80 px-4 py-3 backdrop-blur-md dark:border-stone-800 dark:bg-ink-900/80 lg:hidden">
          <p className="font-display text-lg">IntelliDocs</p>
          <select
            className="rounded-lg border border-stone-300 bg-white px-2 py-1 text-sm dark:border-stone-700 dark:bg-ink-800"
            value={NAV.find((n) => pathname.startsWith(n.href))?.href || "/dashboard"}
            onChange={(e) => {
              window.location.href = e.target.value;
            }}
          >
            {NAV.map((n) => (
              <option key={n.href} value={n.href}>
                {n.label}
              </option>
            ))}
          </select>
        </header>
        <main className="relative mx-auto max-w-6xl px-4 py-8 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
