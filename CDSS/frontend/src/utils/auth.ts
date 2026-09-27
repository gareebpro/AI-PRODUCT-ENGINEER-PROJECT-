/**
 * auth.ts — JWT token helpers for CDSS frontend
 * Centralises all token read/write operations and builds auth headers.
 */

const TOKEN_KEY = 'cdss_token';
const USER_KEY  = 'cdss_username';

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

/** Read the stored JWT from localStorage */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Save JWT + username after a successful login */
export function setSession(token: string, username: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, username);
}

/** Clear token + username on logout */
export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/** Returns true if a token currently exists */
export function isLoggedIn(): boolean {
  return !!getToken();
}

/** Get the stored username */
export function getUsername(): string {
  return localStorage.getItem(USER_KEY) ?? 'Doctor';
}

/**
 * Returns standard headers for authenticated API calls:
 *   { 'Content-Type': 'application/json', Authorization: 'Bearer <token>' }
 */
export function authHeaders(): Record<string, string> {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/**
 * Wrapper around fetch() that:
 *   1. Adds auth headers automatically
 *   2. On 401 Unauthorized → clears session and reloads to /login
 */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = {
    ...authHeaders(),
    ...(options.headers as Record<string, string> ?? {}),
  };

  const res = await fetch(`${BACKEND}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearSession();
    window.location.href = '/login';
  }

  return res;
}
