import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { fakeOrder, renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { OrderDetail } from "./OrderDetail";
import { OrdersList } from "./OrdersList";

vi.mock("next/navigation", async () => (await import("@/test/navigation")).navigationMock());

describe("OrdersList", () => {
  it("asks anonymous visitors to log in", async () => {
    renderWithProviders(<OrdersList />);

    expect(await screen.findByRole("link", { name: /log in/i })).toHaveAttribute("href", "/login?next=/orders");
  });

  it("lists the customer's orders with status and total", async () => {
    server.use(
      http.get("*/backend/orders", () =>
        HttpResponse.json([fakeOrder(), fakeOrder({ id: "o2", status: "delivered", total: 95.5 })]),
      ),
    );
    renderWithProviders(<OrdersList />, { loggedIn: true });

    const links = await screen.findAllByRole("link", { name: /order/i });
    // Newest first.
    expect(links.map((a) => a.getAttribute("href"))).toEqual(["/orders/o2", "/orders/o1"]);
    expect(screen.getByText("Placed")).toBeInTheDocument();
    expect(screen.getByText("Delivered")).toBeInTheDocument();
    expect(screen.getByText("₹95.50")).toBeInTheDocument();
  });

  it("has a friendly empty state", async () => {
    server.use(http.get("*/backend/orders", () => HttpResponse.json([])));
    renderWithProviders(<OrdersList />, { loggedIn: true });

    expect(await screen.findByText(/no orders yet/i)).toBeInTheDocument();
  });
});

describe("OrderDetail", () => {
  it("shows items, total and the status timeline", async () => {
    server.use(
      http.get("*/backend/orders/o1", () =>
        HttpResponse.json(
          fakeOrder({
            status: "dispatched",
            history: [
              { status: "placed", at: "2026-11-21T10:00:00Z", by: "u1" },
              { status: "confirmed", at: "2026-11-21T10:05:00Z", by: "p1" },
              { status: "dispatched", at: "2026-11-21T10:30:00Z", by: "p1" },
            ],
          }),
        ),
      ),
    );
    renderWithProviders(<OrderDetail id="o1" />, { loggedIn: true });

    expect(await screen.findByText(/2 × Paracetamol 500 Tablet/)).toBeInTheDocument();
    expect(screen.getByTestId("order-total")).toHaveTextContent("₹56.20");
    const steps = screen.getAllByRole("listitem").filter((li) => li.dataset.step);
    expect(steps.map((li) => li.dataset.step)).toEqual(["placed", "confirmed", "dispatched"]);
    expect(screen.queryByRole("button", { name: /cancel order/i })).not.toBeInTheDocument();
  });

  it("lets the customer cancel a placed order", async () => {
    let cancelled = false;
    server.use(
      http.get("*/backend/orders/o1", () =>
        HttpResponse.json(fakeOrder({ status: cancelled ? "cancelled" : "placed" })),
      ),
      http.post("*/backend/orders/o1/cancel", () => {
        cancelled = true;
        return HttpResponse.json(fakeOrder({ status: "cancelled" }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<OrderDetail id="o1" />, { loggedIn: true });

    await user.click(await screen.findByRole("button", { name: /cancel order/i }));

    await waitFor(() => expect(cancelled).toBe(true));
    expect(await screen.findByText("Cancelled")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancel order/i })).not.toBeInTheDocument();
  });

  it("explains a missing order", async () => {
    server.use(http.get("*/backend/orders/zzz", () => HttpResponse.json({ detail: "Order not found" }, { status: 404 })));
    renderWithProviders(<OrderDetail id="zzz" />, { loggedIn: true });

    expect(await screen.findByRole("alert")).toHaveTextContent("Order not found");
  });
});
