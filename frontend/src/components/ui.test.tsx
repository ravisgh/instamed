import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { discountPercent, Price, QuantityStepper, StockLabel } from "./ui";

describe("discountPercent", () => {
  it("rounds the saving against MRP", () => {
    expect(discountPercent(28.1, 30.5)).toBe(8);
    expect(discountPercent(30.5, 30.5)).toBe(0);
    expect(discountPercent(31, 30.5)).toBe(0);
    expect(discountPercent(10, 0)).toBe(0);
  });
});

describe("Price", () => {
  it("shows MRP and the discount only when the price is lower", () => {
    const { rerender } = render(<Price price={28.1} mrp={30.5} />);
    expect(screen.getByText("₹28.10")).toBeInTheDocument();
    expect(screen.getByText("₹30.50")).toBeInTheDocument();
    expect(screen.getByText("8% off")).toBeInTheDocument();

    rerender(<Price price={30.5} mrp={30.5} />);
    expect(screen.queryByText(/% off/)).not.toBeInTheDocument();
  });
});

describe("StockLabel", () => {
  it("warns when stock is low", () => {
    const { rerender } = render(<StockLabel quantity={3} />);
    expect(screen.getByText("Only 3 left")).toBeInTheDocument();
    rerender(<StockLabel quantity={40} />);
    expect(screen.getByText("40 in stock")).toBeInTheDocument();
  });
});

describe("QuantityStepper", () => {
  it("steps the quantity and stops at the stock limit", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<QuantityStepper name="Dolo" value={2} max={2} onChange={onChange} />);

    expect(screen.getByRole("button", { name: "Increase quantity of Dolo" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Decrease quantity of Dolo" }));
    expect(onChange).toHaveBeenCalledWith(1);
  });
});
