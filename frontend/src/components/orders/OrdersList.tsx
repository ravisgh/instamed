"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ChevronRightIcon, LockIcon, ReceiptIcon } from "@/components/icons";
import { EmptyState, ErrorBanner, Skeleton, buttonClass } from "@/components/ui";
import type { Order } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { formatDateTime, formatRupees } from "@/lib/format";

import { OrderStatusBadge } from "./OrderStatusBadge";

export function OrdersList() {
  const { status, api } = useAuth();
  const orders = useQuery({
    queryKey: ["orders"],
    queryFn: () => api.get<Order[]>("/orders?limit=50"),
    enabled: status === "authenticated",
  });

  if (status === "anonymous") {
    return (
      <EmptyState icon={<LockIcon />} title="Log in to see your orders">
        <Link href="/login?next=/orders" className={buttonClass("primary", "md", "mt-2")}>
          Log in
        </Link>
      </EmptyState>
    );
  }
  if (orders.isError) return <ErrorBanner message={orders.error.message} />;
  if (status === "loading" || orders.isPending) {
    return (
      <div className="space-y-3" aria-label="Loading orders">
        <Skeleton className="h-20 w-full rounded-2xl" />
        <Skeleton className="h-20 w-full rounded-2xl" />
      </div>
    );
  }
  if (orders.data.length === 0) {
    return (
      <EmptyState icon={<ReceiptIcon />} title="No orders yet.">
        <p>When you place an order it will show up here.</p>
        <Link href="/" className={buttonClass("primary", "md", "mt-4")}>
          Find your medicines
        </Link>
      </EmptyState>
    );
  }

  // Newest first (the API returns oldest first).
  const newestFirst = [...orders.data].reverse();
  return (
    <ul className="space-y-3">
      {newestFirst.map((order) => (
        <li key={order.id}>
          <Link
            href={`/orders/${order.id}`}
            aria-label={`Order of ${formatDateTime(order.created_at)}`}
            className="group flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-card transition hover:border-brand-300 hover:shadow-lift"
          >
            <span className="hidden h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 sm:flex">
              <ReceiptIcon />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-slate-900">{formatDateTime(order.created_at)}</span>
                <OrderStatusBadge status={order.status} />
              </span>
              <span className="mt-0.5 block truncate text-sm text-slate-500">
                {order.items.length} item{order.items.length === 1 ? "" : "s"} · {order.items.map((i) => i.name).join(", ")}
              </span>
            </span>
            <span className="text-right font-bold whitespace-nowrap tabular-nums">{formatRupees(order.total)}</span>
            <ChevronRightIcon className="h-5 w-5 shrink-0 text-slate-300 transition group-hover:text-brand-600" />
          </Link>
        </li>
      ))}
    </ul>
  );
}
