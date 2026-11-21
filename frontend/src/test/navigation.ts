import { vi } from "vitest";

/** Shared spy for router.push; tests assert on it after `vi.mock("next/navigation", ...)`. */
export const push = vi.fn();
export let searchParams = new URLSearchParams();
export const params: Record<string, string> = {};

export function setSearchParams(value: string) {
  searchParams = new URLSearchParams(value);
}

export const navigationMock = () => ({
  useRouter: () => ({ push, replace: push, back: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => searchParams,
  usePathname: () => "/",
  useParams: () => params,
});
