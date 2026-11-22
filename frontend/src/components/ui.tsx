/** Shared presentational building blocks. Keep these dumb: no data fetching here. */
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { formatRupees } from "@/lib/format";

import { AlertIcon, InfoIcon } from "./icons";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-brand-600 text-white shadow-sm hover:bg-brand-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none",
  secondary:
    "border border-slate-300 bg-white text-slate-800 hover:border-slate-400 hover:bg-slate-50 disabled:text-slate-400",
  danger: "border border-rose-300 bg-white text-rose-700 hover:border-rose-400 hover:bg-rose-50 disabled:text-rose-300",
  ghost: "text-slate-700 hover:bg-slate-100 disabled:text-slate-400",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-5 text-base",
};

/** Button styles, also used on links that should look like buttons. */
export function buttonClass(variant: Variant = "primary", size: Size = "md", extra = ""): string {
  return `inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${extra}`;
}

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  return <button className={buttonClass(variant, size, className)} {...props} />;
}

export function Card({ className = "", children }: { className?: string; children: ReactNode }) {
  return <div className={`rounded-2xl border border-slate-200/80 bg-white shadow-card ${className}`}>{children}</div>;
}

/** Standard page shell: centred column with a title row. */
export function Page({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:py-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function RxBadge() {
  return (
    <span
      title="Prescription required"
      className="inline-flex items-center rounded-md bg-rose-50 px-1.5 py-0.5 text-[11px] font-bold tracking-wide text-rose-700 ring-1 ring-rose-200 ring-inset"
    >
      Rx
    </span>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-800">
      <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
      <p>{message}</p>
    </div>
  );
}

const CALLOUT_TONES = {
  info: "border-sky-200 bg-sky-50 text-sky-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  success: "border-brand-200 bg-brand-50 text-brand-800",
} as const;

export function Callout({ tone = "info", children }: { tone?: keyof typeof CALLOUT_TONES; children: ReactNode }) {
  const Icon = tone === "warning" ? AlertIcon : InfoIcon;
  return (
    <div className={`flex items-start gap-2 rounded-xl border px-3.5 py-3 text-sm ${CALLOUT_TONES[tone]}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden="true" className={`animate-pulse rounded-md bg-slate-200/70 ${className}`} />;
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <p className="flex items-center gap-2 text-sm text-slate-500" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      {label}
    </p>
  );
}

export function EmptyState({
  icon,
  title,
  children,
}: {
  icon: ReactNode;
  title: string;
  children?: ReactNode;
}) {
  return (
    <Card className="flex flex-col items-center px-6 py-12 text-center">
      <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 [&>svg]:h-7 [&>svg]:w-7">
        {icon}
      </span>
      <p className="text-base font-semibold text-slate-900">{title}</p>
      {children && <div className="mt-2 text-sm text-slate-500">{children}</div>}
    </Card>
  );
}

/** Whole-number discount of `price` against `mrp`, or 0 when there is none. */
export function discountPercent(price: number, mrp: number): number {
  if (!(mrp > 0) || price >= mrp) return 0;
  return Math.round((1 - price / mrp) * 100);
}

export function Price({ price, mrp }: { price: number; mrp: number }) {
  const off = discountPercent(price, mrp);
  return (
    <span className="flex flex-wrap items-baseline justify-end gap-x-2">
      <span className="text-base font-bold text-slate-900">{formatRupees(price)}</span>
      {off > 0 && (
        <>
          <span className="text-xs text-slate-400 line-through">{formatRupees(mrp)}</span>
          <span className="rounded bg-brand-50 px-1.5 py-0.5 text-[11px] font-bold text-brand-700">{off}% off</span>
        </>
      )}
    </span>
  );
}

export const LOW_STOCK = 5;

export function StockLabel({ quantity }: { quantity: number }) {
  if (quantity <= LOW_STOCK) {
    return <span className="text-xs font-semibold text-amber-700">Only {quantity} left</span>;
  }
  return <span className="text-xs font-medium text-brand-700">{quantity} in stock</span>;
}

export function QuantityStepper({
  name,
  value,
  max,
  onChange,
}: {
  name: string;
  value: number;
  max: number;
  onChange(quantity: number): void;
}) {
  const step = "flex h-9 w-9 items-center justify-center text-lg text-slate-700 hover:bg-slate-100 disabled:opacity-35 disabled:hover:bg-transparent";
  return (
    <span className="inline-flex items-center overflow-hidden rounded-lg border border-slate-300 bg-white">
      <button type="button" aria-label={`Decrease quantity of ${name}`} onClick={() => onChange(value - 1)} className={step}>
        −
      </button>
      <span className="w-8 text-center text-sm font-semibold tabular-nums" aria-live="polite">
        {value}
      </span>
      <button
        type="button"
        aria-label={`Increase quantity of ${name}`}
        disabled={value >= max}
        onClick={() => onChange(value + 1)}
        className={step}
      >
        +
      </button>
    </span>
  );
}
