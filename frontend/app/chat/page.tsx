"use client";

import { Suspense } from "react";
import ChatPage from "./ChatInner";

export default function Page() {
  return (
    <Suspense fallback={<p className="text-sm text-stone-500">Loading chat…</p>}>
      <ChatPage />
    </Suspense>
  );
}
