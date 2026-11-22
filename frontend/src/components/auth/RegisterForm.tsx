"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { LockIcon, MailIcon, UserIcon } from "@/components/icons";
import { Button, ErrorBanner } from "@/components/ui";
import { useAuth } from "@/lib/auth/AuthProvider";

import { AuthCard, Field } from "./AuthCard";
import { errorText } from "./LoginForm";

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
    <AuthCard
      title="Create your account"
      subtitle="Order from the pharmacy near you in a few taps."
      onSubmit={onSubmit}
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-brand-700 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      {error && <ErrorBanner message={error} />}
      <Field label="Full name" icon={<UserIcon />} name="full_name" autoComplete="name" required maxLength={100} />
      <Field label="Email" icon={<MailIcon />} name="email" type="email" autoComplete="email" required />
      <Field
        label="Password"
        icon={<LockIcon />}
        hint="At least 8 characters."
        name="password"
        type="password"
        autoComplete="new-password"
        required
        minLength={8}
        maxLength={72}
      />
      <Button type="submit" size="lg" disabled={busy} className="w-full">
        {busy ? "Creating account…" : "Create account"}
      </Button>
    </AuthCard>
  );
}
