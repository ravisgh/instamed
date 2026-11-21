"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Button, ErrorBanner } from "@/components/ui";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/AuthProvider";

/** Only same-site paths: "/orders" is fine, "https://evil.example" or "//evil" are not. */
export function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") && !next.includes("\\") ? next : "/";
}

export function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    return error.retryAfter ? `${error.message} (wait ${error.retryAfter}s)` : error.message;
  }
  return "Something went wrong. Please try again.";
}

export const inputClass = "mt-1 block w-full rounded-md border border-slate-300 px-3 py-2";

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      router.push(next);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6">
      <h1 className="text-xl font-semibold">Log in</h1>
      {error && <ErrorBanner message={error} />}
      <label className="block text-sm font-medium">
        Email
        <input name="email" type="email" autoComplete="email" required className={inputClass} />
      </label>
      <label className="block text-sm font-medium">
        Password
        <input name="password" type="password" autoComplete="current-password" required className={inputClass} />
      </label>
      <Button type="submit" disabled={busy} className="w-full py-2">
        {busy ? "Logging in…" : "Log in"}
      </Button>
      <p className="text-center text-sm text-slate-600">
        New here?{" "}
        <Link href="/register" className="text-emerald-700 hover:underline">
          Create an account
        </Link>
      </p>
    </form>
  );
}
