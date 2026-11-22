"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { LockIcon, MailIcon } from "@/components/icons";
import { Button, ErrorBanner } from "@/components/ui";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/AuthProvider";

import { AuthCard, Field } from "./AuthCard";

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
    <AuthCard
      title="Welcome back"
      subtitle="Log in to order medicines and track your orders."
      onSubmit={onSubmit}
      footer={
        <>
          New here?{" "}
          <Link href="/register" className="font-semibold text-brand-700 hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      {error && <ErrorBanner message={error} />}
      <Field label="Email" icon={<MailIcon />} name="email" type="email" autoComplete="email" required />
      <Field
        label="Password"
        icon={<LockIcon />}
        name="password"
        type="password"
        autoComplete="current-password"
        required
      />
      <Button type="submit" size="lg" disabled={busy} className="w-full">
        {busy ? "Logging in…" : "Log in"}
      </Button>
    </AuthCard>
  );
}
