import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import type { Mock } from 'vitest';

import App from './App';
import useAuth from './hooks/useAuth';

vi.mock('./hooks/useAuth', async () => {
  const actual = await vi.importActual<typeof import('./hooks/useAuth')>('./hooks/useAuth');
  return {
    __esModule: true,
    ...actual,
    default: vi.fn(),
  };
});

describe('App', () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  test('renders admin login form when user is not authenticated', async () => {
    const checkAuth = vi.fn();
    const mockedUseAuth = useAuth as unknown as Mock;
    mockedUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      currentUser: null,
      loginError: '',
      login: vi.fn().mockResolvedValue(true),
      logout: vi.fn(),
      checkAuth,
    });

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();

      const makeResponse = (payload: unknown) => ({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => payload,
      });

      if (url.includes('/admin/daily-menu/replace')) {
        return Promise.resolve(makeResponse({ message: 'ok' }));
      }

      if (url.includes('/admin/daily-menu/date')) {
        return Promise.resolve(
          makeResponse({
            menu_date: { start_date: '2024-01-01 10:00', end_date: '2024-01-01 22:00', current_date: '2024-01-01 12:00' },
          })
        );
      }

      if (url.includes('/admin/daily-menu')) {
        return Promise.resolve(
          makeResponse({ id: 1, created_at: '2024-01-01T00:00:00Z', note: null, items: [] })
        );
      }

      if (url.includes('/admin/items')) {
        return Promise.resolve(makeResponse({ items: [], total: 0 }));
      }

      if (url.includes('/admin/categories')) {
        return Promise.resolve(makeResponse({ categories: [], total: 0 }));
      }

      if (url.includes('/admin/units')) {
        return Promise.resolve(makeResponse({ units: [], total: 0 }));
      }

      return Promise.resolve(makeResponse({}));
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<App />);

    await waitFor(() => expect(checkAuth).toHaveBeenCalled());

    expect(screen.getByRole('heading', { name: /admin sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });
});
