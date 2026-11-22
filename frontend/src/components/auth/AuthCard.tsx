import type { InputHTMLAttributes, ReactNode } from "react";

import { LogoMark } from "@/components/icons";

/** Centred card shell shared by the login and register screens. */
export function AuthCard({
  title,
  subtitle,
  onSubmit,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  onSubmit(event: React.FormEvent<HTMLFormElement>): void;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="w-full max-w-md">
      <form
        onSubmit={onSubmit}
        className="space-y-5 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lift sm:p-8"
      >
        <div className="flex flex-col items-center text-center">
          <LogoMark className="h-11 w-11" />
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        </div>
        {children}
      </form>
      <p className="mt-5 text-center text-sm text-slate-600">{footer}</p>
    </div>
  );
}

/** A labelled input with a leading icon. The label wraps the input, so it stays accessible by name. */
export function Field({
  label,
  icon,
  hint,
  ...input
}: InputHTMLAttributes<HTMLInputElement> & { label: string; icon: ReactNode; hint?: string }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <span className="relative mt-1.5 block">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400 [&>svg]:h-4.5 [&>svg]:w-4.5">
          {icon}
        </span>
        <input
          className="block h-11 w-full rounded-lg border border-slate-300 bg-white pr-3 pl-10 text-base text-slate-900 shadow-sm transition placeholder:text-slate-400 hover:border-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 focus:outline-none"
          {...input}
        />
      </span>
      {hint && <span className="mt-1 block text-xs font-normal text-slate-500">{hint}</span>}
    </label>
  );
}
