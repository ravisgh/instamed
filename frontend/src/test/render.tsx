import { render } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import { Providers } from "@/app/providers";

import { server } from "./server";

/** Render inside the real app providers, logged out unless a test overrides the session. */
export function renderWithProviders(ui: React.ReactElement) {
  server.use(http.post("*/api/session/refresh", () => HttpResponse.json({ detail: "no" }, { status: 401 })));
  return render(<Providers>{ui}</Providers>);
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
} as const;
