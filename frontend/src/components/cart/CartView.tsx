"use client";

import Link from "next/link";

import { RxBadge } from "@/components/ui";
import { useCart } from "@/lib/cart/CartProvider";
import { formatRupees } from "@/lib/format";

export function CartView() {
  const { cart, total, needsPrescription, setQuantity } = useCart();

  if (cart.lines.length === 0) {
    return (
      <p className="text-slate-600">
        Your cart is empty.{" "}
        <Link href="/" className="text-emerald-700 hover:underline">
          Search medicines
        </Link>
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Delivering to pincode {cart.pincode}</p>
      <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
        {cart.lines.map((line) => (
          <li key={line.medicine_id} className="flex items-center justify-between gap-4 px-4 py-3">
            <span>
              <span className="flex items-center gap-2 font-medium">
                {line.name} {line.prescription_required && <RxBadge />}
              </span>
              <span className="text-sm text-slate-500">
                {line.pack_size} · {formatRupees(line.price)} each
              </span>
            </span>
            <span className="flex items-center gap-2">
              <button
                aria-label={`Decrease quantity of ${line.name}`}
                onClick={() => setQuantity(line.medicine_id, line.quantity - 1)}
                className="h-8 w-8 rounded border border-slate-300 hover:bg-slate-100"
              >
                −
              </button>
              <span className="w-6 text-center tabular-nums">{line.quantity}</span>
              <button
                aria-label={`Increase quantity of ${line.name}`}
                disabled={line.quantity >= line.quantity_available}
                onClick={() => setQuantity(line.medicine_id, line.quantity + 1)}
                className="h-8 w-8 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-40"
              >
                +
              </button>
              <button
                aria-label={`Remove ${line.name}`}
                onClick={() => setQuantity(line.medicine_id, 0)}
                className="ml-2 text-sm text-rose-700 hover:underline"
              >
                Remove
              </button>
            </span>
          </li>
        ))}
      </ul>

      {needsPrescription && (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Your cart needs an approved prescription. You can upload one at checkout.
        </p>
      )}

      <div className="flex items-center justify-between">
        <p className="text-lg">
          Total <span data-testid="cart-total" className="font-semibold">{formatRupees(total)}</span>
        </p>
        <Link href="/checkout" className="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700">
          Checkout
        </Link>
      </div>
    </div>
  );
}
