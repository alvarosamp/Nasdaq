import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';

function mockFetchOnce(status: number, body: unknown) {
  return vi.fn().mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('starts with no user and finishes loading when there is no stored token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
  });

  it('login() stores the token and sets the user', async () => {
    const fakeUser = { id: 1, username: 'pai', is_admin: true, created_at: '2026-01-01T00:00:00Z' };
    global.fetch = mockFetchOnce(200, { access_token: 'abc123', token_type: 'bearer', user: fakeUser });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('pai', 'senha12345');
    });

    expect(result.current.user).toEqual(fakeUser);
    expect(localStorage.getItem('nasdaq_token')).toBe('abc123');
  });

  it('login() with wrong credentials throws and does not set a user', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Usuário ou senha inválidos.' }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await expect(
      act(async () => {
        await result.current.login('pai', 'errada');
      }),
    ).rejects.toThrow();

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('nasdaq_token')).toBeNull();
  });

  it('logout() clears the token and the user', async () => {
    const fakeUser = { id: 1, username: 'pai', is_admin: false, created_at: '2026-01-01T00:00:00Z' };
    global.fetch = mockFetchOnce(200, { access_token: 'abc123', token_type: 'bearer', user: fakeUser });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('pai', 'senha12345');
    });
    expect(result.current.user).not.toBeNull();

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('nasdaq_token')).toBeNull();
  });

  it('rehydrates the user from /api/auth/me when a token already exists on load', async () => {
    localStorage.setItem('nasdaq_token', 'existing-token');
    const fakeUser = { id: 2, username: 'convidado', is_admin: false, created_at: '2026-01-01T00:00:00Z' };
    global.fetch = mockFetchOnce(200, fakeUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toEqual(fakeUser);
  });

  it('clears a stale/invalid token if /api/auth/me returns 401 on load', async () => {
    localStorage.setItem('nasdaq_token', 'expired-token');
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Token inválido ou expirado' }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('nasdaq_token')).toBeNull();
  });
});
