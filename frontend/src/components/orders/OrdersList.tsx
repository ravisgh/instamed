"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ErrorBanner } from "@/components/ui";
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

  if (status === "loading") return <p className="text-slate-500">Loading…</p>;
  if (status === "anonymous") {
    return (
      <p>
        Please{" "}
        <Link href="/login?next=/orders" className="font-medium text-emerald-700 hover:underline">
          log in
        </Link>{" "}
        to see your orders.
      </p>
    );
  }
  if (orders.isError) return <ErrorBanner message={orders.error.message} />;
  if (orders.isPending) return <p className="text-slate-500">Loading orders…</p>;
  if (orders.data.length === 0) {
    return (
      <p className="text-slate-600">
        No orders yet.{" "}
        <Link href="/" className="text-emerald-700 hover:underline">
          Find your medicines
        </Link>
      </p>
    );
  }

  // Newest first (the API returns oldest first).
  const newestFirst = [...orders.data].reverse();
  return (
    <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
      {newestFirst.map((order) => (
        <li key={order.id}>
          <Link
            href={`/orders/${order.id}`}
            aria-label={`Order of ${formatDateTime(order.created_at)}`}
            className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-slate-50"
          >
            <span>
              <span className="block font-medium">
                {order.items.length} item{order.items.length === 1 ? "" : "s"} · {formatDateTime(order.created_at)}
              </span>
              <span className="text-sm text-slate-500">{order.items.map((i) => i.name).join(", ")}</span>
            </span>
            <span className="flex items-center gap-3">
              <OrderStatusBadge status={order.status} />
              <span className="font-semibold">{formatRupees(order.total)}</span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
