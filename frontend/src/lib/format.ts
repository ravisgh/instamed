const rupees = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatRupees(amount: number): string {
  return rupees.format(amount);
}

/** Same rule as the API: 6 digits, first digit 1-9. */
export const PINCODE_PATTERN = /^[1-9][0-9]{5}$/;

export function isValidPincode(value: string): boolean {
  return PINCODE_PATTERN.test(value);
}
