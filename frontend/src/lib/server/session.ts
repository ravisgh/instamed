/**
 * Server-only helpers for the session route handlers (app/api/session/*).
 *
 * The refresh token lives in an httpOnly cookie scoped to /api/session, so browser
 * JavaScript can never read it (XSS cannot steal it) and it is only sent to these
 * routes. The short-lived access token is returned in the JSON body and kept in memory.
 */
import { NextRequest, NextResponse } from "next/server";

export const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";
export const REFRESH_COOKIE = "instamed_rt";
const REFRESH_COOKIE_MAX_AGE = 14 * 24 * 60 * 60; // matches the backend's 14-day default

interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

/** Forward the browser's address so per-IP rate limits on the API see the real client. */
export function forwardHeaders(req: NextRequest): Record<string, string> {
  const forwardedFor = req.headers.get("x-forwarded-for");
  return forwardedFor ? { "x-forwarded-for": forwardedFor } : {};
}

export function readRefreshToken(req: NextRequest): string | undefined {
  return req.cookies.get(REFRESH_COOKIE)?.value;
}

/** Respond with only the access token, storing the refresh token in the cookie. */
export function sessionResponse(tokens: TokenPair): NextResponse {
  const res = NextResponse.json({ access_token: tokens.access_token, expires_in: tokens.expires_in });
  res.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/api/session",
    maxAge: REFRESH_COOKIE_MAX_AGE,
  });
  return res;
}

export function clearSession(res: NextResponse): NextResponse {
  res.cookies.set(REFRESH_COOKIE, "", { httpOnly: true, path: "/api/session", maxAge: 0 });
  return res;
}

/** Copy an API error (status, JSON body, Retry-After) back to the browser unchanged. */
export async function passThroughError(upstream: Response): Promise<NextResponse> {
  const body = await upstream.json().catch(() => ({ detail: "Request failed" }));
  const res = NextResponse.json(body, { status: upstream.status });
  const retryAfter = upstream.headers.get("retry-after");
  if (retryAfter) res.headers.set("retry-after", retryAfter);
  return res;
}
