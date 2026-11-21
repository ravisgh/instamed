import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CartView } from "@/components/cart/CartView";
import { push } from "@/test/navigation";
import { fakeHit, fakeOrder, fakeRxHit, renderWithProviders, seedCart } from "@/test/render";
import { server } from "@/test/server";

import { Checkout } from "./Checkout";

vi.mock("next/navigation", async () => (await import("@/test/navigation")).navigationMock());

beforeEach(() => push.mockClear());

describe("CartView", () => {
  it("shows lines, totals and lets the customer change quantities within stock", async () => {
    seedCart([{ ...fakeHit, quantity: 2 }]);
    const user = userEvent.setup();
    renderWithProviders(<CartView />);

    expect(await screen.findByText("Paracetamol 500 Tablet")).toBeInTheDocument();
    expect(screen.getByTestId("cart-total")).toHaveTextContent("₹56.20");

    await user.click(screen.getByRole("button", { name: /increase/i }));
    expect(screen.getByTestId("cart-total")).toHaveTextContent("₹84.30");
    expect(screen.getByRole("button", { name: /increase/i })).toBeDisabled(); // 3 = stock

    await user.click(screen.getByRole("button", { name: /remove/i }));
    expect(await screen.findByText(/your cart is empty/i)).toBeInTheDocument();
  });

  it("warns when a prescription will be needed", async () => {
    seedCart([{ ...fakeRxHit, quantity: 1 }]);
    renderWithProviders(<CartView />);

    expect(await screen.findByText(/needs an approved prescription/i)).toBeInTheDocument();
  });
});

describe("Checkout", () => {
  it("asks anonymous visitors to log in first", async () => {
    seedCart([{ ...fakeHit, quantity: 1 }]);
    renderWithProviders(<Checkout />);

    const link = await screen.findByRole("link", { name: /log in/i });
    expect(link).toHaveAttribute("href", "/login?next=/checkout");
  });

  it("places an OTC order, clears the cart and opens the order", async () => {
    let body: unknown;
    server.use(
      http.post("*/backend/orders", async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(fakeOrder({ id: "o9" }), { status: 201 });
      }),
    );
    seedCart([{ ...fakeHit, quantity: 2 }]);
    const user = userEvent.setup();
    renderWithProviders(<Checkout />, { loggedIn: true });

    await user.click(await screen.findByRole("button", { name: /place order/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/orders/o9"));
    expect(body).toEqual({ pincode: "201014", items: [{ medicine_id: "m1", quantity: 2 }] });
    expect(JSON.parse(window.localStorage.getItem("instamed.cart.v1") ?? "{}").lines).toEqual([]);
  });

  it("shows API errors such as running out of stock", async () => {
    server.use(
      http.post("*/backend/orders", () =>
        HttpResponse.json({ detail: "Insufficient stock for Paracetamol 500 Tablet" }, { status: 409 }),
      ),
    );
    seedCart([{ ...fakeHit, quantity: 1 }]);
    const user = userEvent.setup();
    renderWithProviders(<Checkout />, { loggedIn: true });

    await user.click(await screen.findByRole("button", { name: /place order/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Insufficient stock for Paracetamol 500 Tablet");
    expect(push).not.toHaveBeenCalled();
  });

  it("requires an approved prescription for Rx items and sends it with the order", async () => {
    let body: { prescription_id?: string } = {};
    server.use(
      http.get("*/backend/prescriptions", () =>
        HttpResponse.json([
          { id: "rx-pending", user_id: "u1", original_filename: "new.pdf", content_type: "application/pdf",
            size_bytes: 10, status: "pending", uploaded_at: "2026-11-21T09:00:00Z" },
          { id: "rx-ok", user_id: "u1", original_filename: "old.pdf", content_type: "application/pdf",
            size_bytes: 10, status: "approved", uploaded_at: "2026-11-20T09:00:00Z" },
        ]),
      ),
      http.post("*/backend/orders", async ({ request }) => {
        body = (await request.json()) as typeof body;
        return HttpResponse.json(fakeOrder({ id: "o7" }), { status: 201 });
      }),
    );
    seedCart([{ ...fakeRxHit, quantity: 1 }]);
    const user = userEvent.setup();
    renderWithProviders(<Checkout />, { loggedIn: true });

    const placeOrder = await screen.findByRole("button", { name: /place order/i });
    expect(placeOrder).toBeDisabled();
    const picker = await screen.findByRole("group", { name: /prescription/i });
    // The list loads after the picker appears, so wait for it. Pending ones cannot be used.
    expect(await within(picker).findByLabelText(/new\.pdf/)).toBeDisabled();

    await user.click(within(picker).getByLabelText(/old\.pdf/));
    await user.click(placeOrder);

    await waitFor(() => expect(push).toHaveBeenCalledWith("/orders/o7"));
    expect(body.prescription_id).toBe("rx-ok");
  });

  it("uploads a new prescription and explains it awaits approval", async () => {
    let uploaded = false;
    server.use(
      http.get("*/backend/prescriptions", () => HttpResponse.json([])),
      http.post("*/backend/prescriptions", () => {
        uploaded = true;
        return HttpResponse.json(
          { id: "rx-new", user_id: "u1", original_filename: "rx.pdf", content_type: "application/pdf",
            size_bytes: 8, status: "pending", uploaded_at: "2026-11-21T11:00:00Z" },
          { status: 201 },
        );
      }),
    );
    seedCart([{ ...fakeRxHit, quantity: 1 }]);
    const user = userEvent.setup();
    renderWithProviders(<Checkout />, { loggedIn: true });

    const file = new File(["%PDF-1.4"], "rx.pdf", { type: "application/pdf" });
    await user.upload(await screen.findByLabelText(/upload a prescription/i), file);

    await waitFor(() => expect(uploaded).toBe(true));
    expect(await screen.findByText(/waiting for a pharmacist/i)).toBeInTheDocument();
  });
});
