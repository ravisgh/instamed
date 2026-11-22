"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import {
  ArrowLeftIcon,
  BadgeCheckIcon,
  CartIcon,
  ChevronRightIcon,
  PillIcon,
  PinIcon,
  SearchIcon,
  ShieldIcon,
  StoreIcon,
} from "@/components/icons";
import {
  Button,
  Callout,
  Card,
  EmptyState,
  ErrorBanner,
  Price,
  QuantityStepper,
  RxBadge,
  Skeleton,
  StockLabel,
  buttonClass,
} from "@/components/ui";
import type { Medicine, MedicineSearchResponse, StockSearchResponse } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { useCart } from "@/lib/cart/CartProvider";
import { formatRupees, isValidPincode } from "@/lib/format";
import { useDebounced, usePincode } from "@/lib/hooks";

/** Generic salt names only: a starting point, not a recommendation. */
export const POPULAR_SEARCHES = ["Paracetamol", "Cetirizine", "Pantoprazole", "Azithromycin", "Vitamin D3"];

const TRUST = [
  { icon: ShieldIcon, title: "Pharmacist-verified", text: "Every prescription is checked" },
  { icon: BadgeCheckIcon, title: "Genuine medicines", text: "From a licensed pharmacy" },
  { icon: StoreIcon, title: "Live stock", text: "Real availability at your pincode" },
];

export function SearchPage() {
  const { api } = useAuth();
  const [pincode, setPincode] = usePincode();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Medicine | null>(null);
  const term = useDebounced(query.trim());

  const search = useQuery({
    queryKey: ["medicine-search", term],
    queryFn: () =>
      api.get<MedicineSearchResponse>(`/medicines/search?q=${encodeURIComponent(term)}&limit=10`),
    enabled: term.length >= 2,
  });

  function changeQuery(value: string) {
    setQuery(value);
    setSelected(null);
  }

  return (
    <>
      <section className="relative overflow-hidden border-b border-brand-100 bg-gradient-to-br from-brand-50 via-white to-sky-50">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-brand-200/40 blur-3xl"
        />
        <div className="relative mx-auto max-w-5xl px-4 pt-10 pb-8 sm:pt-14 sm:pb-10">
          <p className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-brand-700 ring-1 ring-brand-200">
            <PinIcon className="h-3.5 w-3.5" /> Delivered from a pharmacy near you
          </p>
          <h1 className="max-w-3xl text-3xl font-extrabold tracking-tight text-balance text-slate-900 sm:text-4xl">
            Medicines from the pharmacy <span className="whitespace-nowrap text-brand-600">nearest you</span>
          </h1>
          <p className="mt-2 max-w-xl text-slate-600">
            Search by name, salt or brand. See live stock and price at your pincode.
          </p>

          <div className="mt-6 flex flex-col gap-2 rounded-2xl bg-white p-2 shadow-lift ring-1 ring-slate-200 sm:flex-row">
            <label className="flex items-center gap-2 rounded-xl px-3 py-2 focus-within:bg-brand-50/60 focus-within:ring-2 focus-within:ring-brand-500/40 sm:w-48">
              <PinIcon className="h-5 w-5 shrink-0 text-brand-600" />
              <span className="flex flex-col">
                <span className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Delivery pincode</span>
                <input
                  inputMode="numeric"
                  maxLength={6}
                  value={pincode}
                  onChange={(e) => setPincode(e.target.value.replace(/\D/g, ""))}
                  placeholder="201014"
                  className="w-full bg-transparent text-base font-semibold text-slate-900 outline-none focus-visible:outline-none placeholder:font-normal placeholder:text-slate-400"
                />
              </span>
            </label>
            <label className="flex flex-1 items-center gap-2 rounded-xl px-3 py-2 focus-within:bg-brand-50/60 focus-within:ring-2 focus-within:ring-brand-500/40">
              <SearchIcon className="h-5 w-5 shrink-0 text-slate-400" />
              <span className="flex flex-1 flex-col">
                <span className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Search medicines</span>
                <input
                  type="search"
                  value={query}
                  onChange={(e) => changeQuery(e.target.value)}
                  placeholder="Name, salt or brand (typos are fine)"
                  className="w-full bg-transparent text-base text-slate-900 outline-none focus-visible:outline-none placeholder:text-slate-400"
                />
              </span>
            </label>
          </div>

          {query.trim().length === 0 && (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-sm text-slate-500">Popular:</span>
              {POPULAR_SEARCHES.map((name) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => changeQuery(name)}
                  className="rounded-full bg-white px-3 py-1.5 text-sm font-medium text-slate-700 ring-1 ring-slate-200 hover:text-brand-700 hover:ring-brand-300"
                >
                  {name}
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      <div className="mx-auto w-full max-w-5xl px-4 py-8">
        {search.isError && <ErrorBanner message={search.error.message} />}

        {selected ? (
          <Availability medicine={selected} pincode={pincode} onBack={() => setSelected(null)} />
        ) : term.length < 2 ? (
          <ul className="grid gap-3 sm:grid-cols-3">
            {TRUST.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-card">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <Icon />
                </span>
                <span>
                  <span className="block text-sm font-semibold text-slate-900">{title}</span>
                  <span className="block text-xs text-slate-500">{text}</span>
                </span>
              </li>
            ))}
          </ul>
        ) : search.isLoading ? (
          <ResultSkeleton />
        ) : search.data && search.data.results.length === 0 ? (
          <EmptyState icon={<SearchIcon />} title={`No medicines match “${term}”`}>
            Check the spelling, or try the salt name (for example “paracetamol”).
          </EmptyState>
        ) : search.data ? (
          <section aria-label="Search results">
            <p className="mb-3 text-sm text-slate-500">
              {search.data.results.length} result{search.data.results.length === 1 ? "" : "s"} for “{term}”
            </p>
            <ul className="space-y-2">
              {search.data.results.map((m) => (
                <li key={m.id}>
                  <button
                    onClick={() => setSelected(m)}
                    className="group flex w-full items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-3 pr-4 text-left shadow-card transition hover:border-brand-300 hover:shadow-lift sm:p-4"
                  >
                    <PillTile />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2 font-semibold text-slate-900">
                        <span className="truncate">{m.name}</span>
                        {m.prescription_required && <RxBadge />}
                      </span>
                      <span className="block truncate text-sm text-slate-500">
                        {m.pack_size} · {m.composition}
                      </span>
                    </span>
                    <span className="text-right">
                      <span className="block text-xs text-slate-400">MRP</span>
                      <span className="block text-sm font-semibold whitespace-nowrap text-slate-800">
                        {formatRupees(m.mrp)}
                      </span>
                    </span>
                    <ChevronRightIcon className="h-5 w-5 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-600" />
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </>
  );
}

function PillTile({ large = false }: { large?: boolean }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-50 to-sky-50 text-brand-600 ring-1 ring-brand-100 ${
        large ? "h-16 w-16 [&>svg]:h-8 [&>svg]:w-8" : "h-12 w-12 [&>svg]:h-6 [&>svg]:w-6"
      }`}
    >
      <PillIcon />
    </span>
  );
}

function ResultSkeleton() {
  return (
    <ul className="space-y-2" aria-label="Loading results">
      {[0, 1, 2].map((i) => (
        <li key={i} className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-4">
          <Skeleton className="h-12 w-12 rounded-xl" />
          <span className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </span>
          <Skeleton className="h-4 w-14" />
        </li>
      ))}
    </ul>
  );
}

function Availability({ medicine, pincode, onBack }: { medicine: Medicine; pincode: string; onBack(): void }) {
  const { api } = useAuth();
  const cart = useCart();
  const validPincode = isValidPincode(pincode);

  const stock = useQuery({
    queryKey: ["stock", pincode, medicine.name],
    queryFn: () =>
      api.get<StockSearchResponse>(
        `/search?pincode=${pincode}&medicine_name=${encodeURIComponent(medicine.name)}`,
      ),
    enabled: validPincode,
  });

  return (
    <section className="space-y-4">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 rounded-lg text-sm font-medium text-brand-700 hover:text-brand-800"
      >
        <ArrowLeftIcon className="h-4 w-4" /> Back to results
      </button>

      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <PillTile large />
          <div className="min-w-0">
            <h2 className="flex flex-wrap items-center gap-2 text-xl font-bold tracking-tight text-slate-900">
              {medicine.name} {medicine.prescription_required && <RxBadge />}
            </h2>
            <p className="mt-0.5 text-sm text-slate-600">{medicine.composition}</p>
            <p className="text-xs text-slate-400">by {medicine.manufacturer}</p>
          </div>
        </div>

        <div className="mt-5 border-t border-slate-100 pt-4">
          <p className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-slate-700">
            <PinIcon className="h-4 w-4 text-brand-600" />
            {validPincode ? `Available at ${pincode}` : "Availability"}
          </p>

          {!validPincode && <ErrorBanner message="Enter a valid 6-digit pincode to check stock near you." />}
          {stock.isPending && validPincode && (
            <div className="space-y-2" aria-label="Checking stock">
              <Skeleton className="h-14 w-full rounded-xl" />
            </div>
          )}
          {stock.isError && <ErrorBanner message={stock.error.message} />}

          {stock.data && (
            <ul className="space-y-2">
              {stock.data.results.map((hit) => {
                const inCart = cart.cart.storeId === stock.data.store_id
                  ? cart.cart.lines.find((l) => l.medicine_id === hit.medicine_id)
                  : undefined;
                return (
                  <li
                    key={hit.medicine_id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-3 sm:flex-nowrap sm:p-4"
                  >
                    <span>
                      <span className="block font-semibold text-slate-900">{hit.pack_size}</span>
                      <StockLabel quantity={hit.quantity_available} />
                    </span>
                    <span className="flex items-center gap-4">
                      <Price price={hit.price} mrp={hit.mrp} />
                      {inCart ? (
                        <QuantityStepper
                          name={hit.name}
                          value={inCart.quantity}
                          max={hit.quantity_available}
                          onChange={(q) => cart.setQuantity(hit.medicine_id, q)}
                        />
                      ) : (
                        <Button onClick={() => cart.add(hit, stock.data.store_id, stock.data.pincode)}>
                          <CartIcon className="h-4 w-4" /> Add to cart
                        </Button>
                      )}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
          {stock.data && cart.count > 0 && (
            <div className="mt-3 flex justify-end">
              <Link href="/cart" className={buttonClass("secondary", "sm")}>
                View cart ({cart.count}) <ChevronRightIcon className="h-4 w-4" />
              </Link>
            </div>
          )}
        </div>
      </Card>

      {medicine.prescription_required && (
        <Callout>
          This is a prescription medicine. You can add it now and upload your prescription at checkout; a
          pharmacist approves it before the order is placed.
        </Callout>
      )}
    </section>
  );
}
