"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth/AuthProvider";
import { useCart } from "@/lib/cart/CartProvider";

import { CartIcon, LogoMark, LogoutIcon, ReceiptIcon } from "./icons";
import { buttonClass } from "./ui";

function initials(name: string | undefined): string {
  const parts = (name ?? "").trim().split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase() || "?";
}

const navLink =
  "inline-flex h-10 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900";

export function Header() {
  const { status, user, logout } = useAuth();
  const { count } = useCart();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70">
      <nav className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-3 px-4">
        <Link href="/" className="flex items-center gap-2 rounded-lg" aria-label="InstaMed home">
          <LogoMark />
          <span className="text-lg font-extrabold tracking-tight text-slate-900">
            Insta<span className="text-brand-600">Med</span>
          </span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-2">
          <Link href="/cart" className={navLink} aria-label={count > 0 ? `Cart, ${count} items` : "Cart"}>
            <span className="relative">
              <CartIcon />
              {count > 0 && (
                <span className="absolute -top-2 -right-2.5 flex h-4.5 min-w-4.5 items-center justify-center rounded-full bg-brand-600 px-1 text-[10px] font-bold text-white ring-2 ring-white">
                  {count}
                </span>
              )}
            </span>
            <span className="hidden sm:inline">Cart</span>
          </Link>

          {status === "authenticated" ? (
            <>
              <Link href="/orders" className={navLink}>
                <ReceiptIcon />
                <span className="hidden sm:inline">My orders</span>
                <span className="sr-only sm:hidden">My orders</span>
              </Link>
              <span
                title={user?.full_name}
                className="ml-1 hidden h-9 items-center gap-2 rounded-full bg-slate-100 py-1 pr-3 pl-1 sm:inline-flex"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
                  {initials(user?.full_name)}
                </span>
                <span className="max-w-32 truncate text-sm font-medium text-slate-700">{user?.full_name}</span>
              </span>
              <button onClick={() => logout()} className={`${navLink} hover:text-rose-700`}>
                <LogoutIcon />
                <span className="hidden sm:inline">Log out</span>
                <span className="sr-only sm:hidden">Log out</span>
              </button>
            </>
          ) : status === "anonymous" ? (
            <>
              <Link href="/login" className={navLink}>
                Log in
              </Link>
              <Link href="/register" className={buttonClass("primary", "md")}>
                Sign up
              </Link>
            </>
          ) : (
            <span className="h-9 w-28 animate-pulse rounded-lg bg-slate-100" aria-hidden="true" />
          )}
        </div>
      </nav>
    </header>
  );
}
