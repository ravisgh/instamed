/** Small shared presentational pieces. */
import type { ButtonHTMLAttributes } from "react";

export function RxBadge() {
  return (
    <span
      title="Prescription required"
      className="rounded bg-rose-100 px-1.5 py-0.5 text-xs font-semibold text-rose-700"
    >
      Rx
    </span>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <p role="alert" className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
      {message}
    </p>
  );
}

export function Button({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300 ${className}`}
      {...props}
    />
  );
}
