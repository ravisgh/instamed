import { describe, expect, it } from "vitest";

import { formatRupees, isValidPincode } from "./format";

describe("formatRupees", () => {
  it("formats Indian rupees with two decimals", () => {
    expect(formatRupees(32.28)).toBe("₹32.28");
    expect(formatRupees(1234567.5)).toBe("₹12,34,567.50");
  });
});

describe("isValidPincode", () => {
  it.each(["201014", "560038", "110001"])("accepts %s", (pin) => {
    expect(isValidPincode(pin)).toBe(true);
  });

  it.each(["", "20101", "2010145", "060038", "20101a"])("rejects %j", (pin) => {
    expect(isValidPincode(pin)).toBe(false);
  });
});
