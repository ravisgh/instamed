import { render } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import { Providers } from "@/app/providers";

import { server } from "./server";

export const fakeUser = {
  id: "u1",
  email: "asha@example.com",
  full_name: "Asha Verma",
  role: "customer",
  is_active: true,
} as const;

/** Render inside the real app providers; logged out unless `loggedIn` is set. */
export function renderWithProviders(ui: React.ReactElement, { loggedIn = false } = {}) {
  server.use(
    http.post("*/api/session/refresh", () =>
      loggedIn
        ? HttpResponse.json({ access_token: "test-token", expires_in: 900 })
        : HttpResponse.json({ detail: "no" }, { status: 401 }),
    ),
    http.get("*/backend/auth/me", () => HttpResponse.json(fakeUser)),
  );
  return render(<Providers>{ui}</Providers>);
}

/** Put a cart in localStorage before rendering (the provider loads it on mount). */
export function seedCart(lines: Array<typeof fakeHit & { quantity: number }>, storeId = "s1") {
  window.localStorage.setItem(
    "instamed.cart.v1",
    JSON.stringify({ storeId, pincode: "201014", lines }),
  );
}

export const fakeMedicine = {
  id: "m1",
  name: "Paracetamol 500 Tablet",
  composition: "Paracetamol (500mg)",
  manufacturer: "Example Pharma",
  pack_size: "15 Tablet",
  mrp: 30.5,
  schedule: "OTC",
  prescription_required: false,
  gst_percent: 5,
  hsn_code: "30049099",
} as const;

export const fakeHit = {
  medicine_id: "m1",
  name: "Paracetamol 500 Tablet",
  pack_size: "15 Tablet",
  mrp: 30.5,
  price: 28.1,
  quantity_available: 3,
  prescription_required: false,
};

export const fakeRxHit = {
  medicine_id: "m2",
  name: "Amoxicillin 500 Capsule",
  pack_size: "10 Capsule",
  mrp: 99,
  price: 95.5,
  quantity_available: 5,
  prescription_required: true,
};

export function fakeOrder(overrides: Record<string, unknown> = {}) {
  return {
    id: "o1",
    user_id: "u1",
    store_id: "s1",
    pincode: "201014",
    items: [
      {
        medicine_id: "m1",
        name: "Paracetamol 500 Tablet",
        pack_size: "15 Tablet",
        quantity: 2,
        unit_price: 28.1,
        line_total: 56.2,
      },
    ],
    total: 56.2,
    status: "placed",
    prescription_id: null,
    created_at: "2026-11-21T10:00:00Z",
    updated_at: "2026-11-21T10:00:00Z",
    history: [{ status: "placed", at: "2026-11-21T10:00:00Z", by: "u1" }],
    ...overrides,
  };
}
