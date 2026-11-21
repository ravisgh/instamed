"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button, ErrorBanner, RxBadge } from "@/components/ui";
import type { Medicine, MedicineSearchResponse, StockSearchResponse } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { useCart } from "@/lib/cart/CartProvider";
import { formatRupees, isValidPincode } from "@/lib/format";
import { useDebounced, usePincode } from "@/lib/hooks";

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

  return (
    <div className="space-y-6">
      <section className="grid gap-3 sm:grid-cols-[10rem_1fr]">
        <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
          Delivery pincode
          <input
            inputMode="numeric"
            maxLength={6}
            value={pincode}
            onChange={(e) => setPincode(e.target.value.replace(/\D/g, ""))}
            placeholder="201014"
            className="rounded-md border border-slate-300 px-3 py-2 text-base"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
          Search medicines
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelected(null);
            }}
            placeholder="Name, salt or brand (typos are fine)"
            className="rounded-md border border-slate-300 px-3 py-2 text-base"
          />
        </label>
      </section>

      {search.isError && <ErrorBanner message={search.error.message} />}

      {selected ? (
        <Availability medicine={selected} pincode={pincode} onBack={() => setSelected(null)} />
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {search.data?.results.map((m) => (
            <li key={m.id}>
              <button
                onClick={() => setSelected(m)}
                className="flex w-full items-start justify-between gap-4 px-4 py-3 text-left hover:bg-slate-50"
              >
                <span>
                  <span className="flex items-center gap-2 font-medium text-slate-900">
                    {m.name} {m.prescription_required && <RxBadge />}
                  </span>
                  <span className="block text-sm text-slate-500">
                    {m.pack_size} · {m.composition}
                  </span>
                </span>
                <span className="whitespace-nowrap text-sm text-slate-600">MRP {formatRupees(m.mrp)}</span>
              </button>
            </li>
          ))}
          {search.data && search.data.results.length === 0 && (
            <li className="px-4 py-3 text-sm text-slate-500">No medicines match “{term}”.</li>
          )}
        </ul>
      )}
    </div>
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
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <button onClick={onBack} className="text-sm text-emerald-700 hover:underline">
        ← Back to results
      </button>
      <h2 className="flex items-center gap-2 text-lg font-semibold">
        {medicine.name} {medicine.prescription_required && <RxBadge />}
      </h2>
      <p className="text-sm text-slate-600">
        {medicine.composition} · {medicine.manufacturer}
      </p>

      {!validPincode && <ErrorBanner message="Enter a valid 6-digit pincode to check stock near you." />}
      {stock.isPending && validPincode && <p className="text-sm text-slate-500">Checking stock…</p>}
      {stock.isError && <ErrorBanner message={stock.error.message} />}

      {stock.data && (
        <ul className="divide-y divide-slate-100">
          {stock.data.results.map((hit) => (
            <li key={hit.medicine_id} className="flex items-center justify-between gap-4 py-2">
              <span>
                <span className="block font-medium">{hit.pack_size}</span>
                <span className="text-sm text-slate-500">{hit.quantity_available} in stock</span>
              </span>
              <span className="flex items-center gap-3">
                <span className="text-right">
                  <span className="block font-semibold">{formatRupees(hit.price)}</span>
                  {hit.price < hit.mrp && (
                    <span className="text-xs text-slate-400 line-through">{formatRupees(hit.mrp)}</span>
                  )}
                </span>
                <Button onClick={() => cart.add(hit, stock.data.store_id, stock.data.pincode)}>Add to cart</Button>
              </span>
            </li>
          ))}
        </ul>
      )}
      {medicine.prescription_required && (
        <p className="text-xs text-slate-500">You will need an approved prescription to order this.</p>
      )}
    </section>
  );
}
