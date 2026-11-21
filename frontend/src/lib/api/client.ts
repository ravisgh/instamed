/**
 * Browser-side API client. Every call goes to /backend/* on our own origin, which
 * next.config.ts rewrites to the FastAPI server, so no CORS is involved.
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public requestId: string | null,
    public retryAfter: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface TokenSource {
  getAccessToken(): string | null;
  /** Get a fresh access token (or null when the session is gone). */
  refreshAccessToken(): Promise<string | null>;
}

type ValidationIssue = { loc?: (string | number)[]; msg?: string };

function describe(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI 422: [{loc: ["body", "field"], msg: "..."}]
    return (detail as ValidationIssue[])
      .map((issue) => {
        const field = issue.loc?.filter((part) => part !== "body").join(".");
        return field ? `${field}: ${issue.msg}` : String(issue.msg);
      })
      .join("; ");
  }
  return `Request failed (${status})`;
}

export async function toApiError(res: Response): Promise<ApiError> {
  const body = (await res.json().catch(() => ({}))) as { detail?: unknown };
  const retryAfter = res.headers.get("retry-after");
  return new ApiError(
    res.status,
    describe(body.detail, res.status),
    res.headers.get("x-request-id"),
    retryAfter ? Number(retryAfter) : null,
  );
}

export type ApiClient = ReturnType<typeof createApiClient>;

export function createApiClient(tokens: TokenSource, baseUrl = "/backend") {
  async function request<T>(method: string, path: string, body?: unknown, retried = false): Promise<T> {
    const headers = new Headers();
    const token = tokens.getAccessToken();
    if (token) headers.set("authorization", `Bearer ${token}`);

    let payload: BodyInit | undefined;
    if (body instanceof FormData) {
      payload = body; // the browser sets the multipart boundary itself
    } else if (body !== undefined) {
      headers.set("content-type", "application/json");
      payload = JSON.stringify(body);
    }

    const res = await fetch(`${baseUrl}${path}`, { method, headers, body: payload });

    if (res.status === 401 && !retried) {
      const fresh = await tokens.refreshAccessToken();
      if (fresh) return request<T>(method, path, body, true);
    }
    if (!res.ok) throw await toApiError(res);
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }

  return {
    get: <T>(path: string) => request<T>("GET", path),
    post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
    patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
    /** Fetch a binary file (e.g. a prescription) with auth, as a Blob. */
    blob: async (path: string): Promise<Blob> => {
      const headers = new Headers();
      const token = tokens.getAccessToken();
      if (token) headers.set("authorization", `Bearer ${token}`);
      const res = await fetch(`${baseUrl}${path}`, { headers });
      if (!res.ok) throw await toApiError(res);
      return res.blob();
    },
  };
}
