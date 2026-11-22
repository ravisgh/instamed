"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { CartIcon, ChevronRightIcon, PillIcon, PinIcon, TrashIcon } from "@/components/icons";
import { Callout, Card, EmptyState, QuantityStepper, RxBadge, buttonClass } from "@/components/ui";
import { useCart } from "@/lib/cart/CartProvider";
import { formatRupees } from "@/lib/format";

export function CartView() {
  const { cart, count, total, needsPrescription, setQuantity } = useCart();

  if (cart.lines.length === 0) {
    return (
      <EmptyState icon={<CartIcon />} title="Your cart is empty">
        <p>Search for a medicine and add it from the pharmacy near you.</p>
        <Link href="/" className={buttonClass("primary", "md", "mt-4")}>
          Search medicines
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-3">
        <p className="flex items-center gap-1.5 text-sm text-slate-500">
          <PinIcon className="h-4 w-4 text-brand-600" /> Delivering to pincode{" "}
          <span className="font-semibold text-slate-700">{cart.pincode}</span>
        </p>
        <ul className="space-y-3">
          {cart.lines.map((line) => (
            <li key={line.medicine_id}>
              <Card className="flex flex-wrap items-center gap-4 p-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <PillIcon className="h-6 w-6" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2 font-semibold text-slate-900">
                    <span className="truncate">{line.name}</span>
                    {line.prescription_required && <RxBadge />}
                  </span>
                  <span className="block text-sm text-slate-500">
                    {line.pack_size} · {formatRupees(line.price)} each
                  </span>
                </span>
                <span className="flex w-full items-center justify-between gap-3 sm:w-auto">
                  <QuantityStepper
                    name={line.name}
                    value={line.quantity}
                    max={line.quantity_available}
                    onChange={(q) => setQuantity(line.medicine_id, q)}
                  />
                  <span className="w-20 text-right font-semibold tabular-nums">
                    {formatRupees(Math.round(line.price * 100 * line.quantity) / 100)}
                  </span>
                  <button
                    aria-label={`Remove ${line.name}`}
                    onClick={() => setQuantity(line.medicine_id, 0)}
                    className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                  >
                    <TrashIcon className="h-4.5 w-4.5" />
                  </button>
                </span>
              </Card>
            </li>
          ))}
        </ul>

        {needsPrescription && (
          <Callout tone="warning">Your cart needs an approved prescription. You can upload one at checkout.</Callout>
        )}
      </div>

      <OrderSummary count={count} total={<span data-testid="cart-total">{formatRupees(total)}</span>}>
        <Link href="/checkout" className={buttonClass("primary", "lg", "w-full")}>
          Checkout <ChevronRightIcon className="h-4 w-4" />
        </Link>
      </OrderSummary>
    </div>
  );
}

/** The sticky price summary used by the cart and checkout pages. */
export function OrderSummary({
  count,
  total,
  children,
}: {
  count: number;
  total: ReactNode;
  children?: ReactNode;
}) {
  return (
    <Card className="p-5 lg:sticky lg:top-24">
      <h2 className="mb-4 text-base font-bold text-slate-900">Order summary</h2>
      <dl className="space-y-2 text-sm">
        <div className="flex justify-between text-slate-600">
          <dt>Items</dt>
          <dd className="tabular-nums">{count}</dd>
        </div>
        <div className="flex justify-between text-slate-600">
          <dt>Delivery</dt>
          <dd className="font-medium text-brand-700">Free</dd>
        </div>
        <div className="flex justify-between border-t border-slate-100 pt-3 text-base font-bold text-slate-900">
          <dt>Total</dt>
          <dd className="tabular-nums">{total}</dd>
        </div>
      </dl>
      {children && <div className="mt-5 space-y-3">{children}</div>}
    </Card>
  );
}
