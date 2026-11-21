import type { TokenSource } from "@/lib/api/client";

/**
 * Holds the in-memory access token and refreshes it through /api/session/refresh.
 *
 * Refresh tokens rotate and a reused one revokes the whole session, so concurrent
 * refreshes (React StrictMode, several requests hitting 401 at once) share one request.
 */
export class SessionTokens implements TokenSource {
  private token: string | null = null;
  private inFlight: Promise<string | null> | null = null;

  constructor(private readonly onSignedOut: () => void) {}

  getAccessToken(): string | null {
    return this.token;
  }

  setAccessToken(token: string | null): void {
    this.token = token;
  }

  refreshAccessToken(): Promise<string | null> {
    this.inFlight ??= fetch("/api/session/refresh", { method: "POST" })
      .then(async (res) => (res.ok ? ((await res.json()) as { access_token: string }).access_token : null))
      .catch(() => null)
      .then((token) => {
        this.token = token;
        if (!token) this.onSignedOut();
        return token;
      })
      .finally(() => {
        this.inFlight = null;
      });
    return this.inFlight;
  }
}
