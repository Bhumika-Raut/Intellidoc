"use client";

import { ThemeProvider } from "next-themes";
import { ToastProvider } from "./Toast";
import { AppShell } from "./AppShell";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <ToastProvider>
        <AppShell>{children}</AppShell>
      </ToastProvider>
    </ThemeProvider>
  );
}
