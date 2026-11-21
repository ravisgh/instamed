import type { StockHit } from "@/lib/api/types";

/** A cart belongs to one store: the one that serves the customer's pincode. */
export interface CartLine extends StockHit {
  quantity: number;
}

export interface CartState {
  storeId: string | null;
  pincode: string | null;
  lines: CartLine[];
}

export type CartAction =
  | { type: "add"; hit: StockHit; storeId: string; pincode: string }
  | { type: "setQuantity"; medicineId: string; quantity: number }
  | { type: "clear" }
  | { type: "load"; state: CartState };

export const EMPTY_CART: CartState = { storeId: null, pincode: null, lines: [] };

function clamp(quantity: number, line: StockHit): number {
  return Math.max(0, Math.min(quantity, line.quantity_available));
}

export function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case "add": {
      // Stock and prices are per store, so switching store starts a fresh cart.
      const base = state.storeId === action.storeId ? state : { ...EMPTY_CART, storeId: action.storeId };
      const existing = base.lines.find((l) => l.medicine_id === action.hit.medicine_id);
      const lines = existing
        ? base.lines.map((l) =>
            l.medicine_id === action.hit.medicine_id
              ? { ...l, ...action.hit, quantity: clamp(l.quantity + 1, action.hit) }
              : l,
          )
        : [...base.lines, { ...action.hit, quantity: clamp(1, action.hit) }];
      return { storeId: action.storeId, pincode: action.pincode, lines: lines.filter((l) => l.quantity > 0) };
    }
    case "setQuantity": {
      const lines = state.lines
        .map((l) => (l.medicine_id === action.medicineId ? { ...l, quantity: clamp(action.quantity, l) } : l))
        .filter((l) => l.quantity > 0);
      return lines.length ? { ...state, lines } : EMPTY_CART;
    }
    case "clear":
      return EMPTY_CART;
    case "load": {
      // Saved carts come from localStorage: keep only well-formed lines within stock.
      const saved = Array.isArray(action.state?.lines) ? action.state.lines : [];
      const lines = saved
        .filter((l) => typeof l?.medicine_id === "string" && typeof l?.price === "number")
        .map((l) => ({ ...l, quantity: clamp(l.quantity, l) }))
        .filter((l) => l.quantity > 0);
      return lines.length && action.state?.storeId
        ? { storeId: action.state.storeId, pincode: action.state.pincode, lines }
        : EMPTY_CART;
    }
  }
}

const toPaise = (rupees: number) => Math.round(rupees * 100);

export function cartTotal(state: CartState): number {
  return state.lines.reduce((sum, l) => sum + toPaise(l.price) * l.quantity, 0) / 100;
}

export function itemCount(state: CartState): number {
  return state.lines.reduce((sum, l) => sum + l.quantity, 0);
}

export function needsPrescription(state: CartState): boolean {
  return state.lines.some((l) => l.prescription_required);
}
