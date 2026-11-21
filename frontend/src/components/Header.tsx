"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth/AuthProvider";
import { useCart } from "@/lib/cart/CartProvider";

export function Header() {
  const { status, user, logout } = useAuth();
  const { count } = useCart();

  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="text-lg font-bold text-emerald-700">
          InstaMed
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link href="/cart" className="hover:text-emerald-700">
            Cart{count > 0 && <span className="ml-1 rounded-full bg-emerald-600 px-2 text-white">{count}</span>}
          </Link>
          {status === "authenticated" ? (
            <>
              <Link href="/orders" className="hover:text-emerald-700">
                My orders
              </Link>
              <span className="text-slate-500">{user?.full_name}</span>
              <button onClick={() => logout()} className="text-slate-600 hover:text-rose-700">
                Log out
              </button>
            </>
          ) : status === "anonymous" ? (
            <>
              <Link href="/login" className="hover:text-emerald-700">
                Log in
              </Link>
              <Link href="/register" className="rounded-md bg-emerald-600 px-3 py-1.5 text-white hover:bg-emerald-700">
                Sign up
              </Link>
            </>
          ) : null}
        </div>
      </nav>
    </header>
  );
}
