"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, ErrorBanner } from "@/components/ui";
import { useAuth } from "@/lib/auth/AuthProvider";

import { errorText, inputClass } from "./LoginForm";

export function RegisterForm() {
  const { register } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await register({
        full_name: String(form.get("full_name")),
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      router.push("/");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6">
      <h1 className="text-xl font-semibold">Create your account</h1>
      {error && <ErrorBanner message={error} />}
      <label className="block text-sm font-medium">
        Full name
        <input name="full_name" autoComplete="name" required maxLength={100} className={inputClass} />
      </label>
      <label className="block text-sm font-medium">
        Email
        <input name="email" type="email" autoComplete="email" required className={inputClass} />
      </label>
      <label className="block text-sm font-medium">
        Password
        <input
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
          className={inputClass}
        />
        <span className="mt-1 block text-xs font-normal text-slate-500">At least 8 characters.</span>
      </label>
      <Button type="submit" disabled={busy} className="w-full py-2">
        {busy ? "Creating account…" : "Create account"}
      </Button>
      <p className="text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="text-emerald-700 hover:underline">
          Log in
        </Link>
      </p>
    </form>
  );
}
