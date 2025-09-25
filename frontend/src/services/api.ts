import {
  AppImage,
  Category,
  CategoryListResponse,
  DailyMenuResponse,
  ImageListResponse,
  Item,
  ItemListResponse,
  MenuDateResponse,
  SuccessResponse,
  Unit,
  UnitListResponse,
} from '../types/types';
import { getAuthHeaders } from '../hooks/useAuth';
import { withBase } from './config';

export type ApiError = {
  status: number;
  detail: string;
  error_code?: string;
  retry_after?: number;
  rate_limit?: {
    limit?: number;
    window?: number;
    remaining?: number;
    reset?: number;
  };
  raw?: unknown;
};

type RateLimitMeta = {
  limit?: number;
  window?: number;
  remaining?: number;
  reset?: number;
  retry_after?: number;
};

function parseRateLimitHeaders(res: Response): RateLimitMeta {
  const h = res.headers;
  const limit = Number(h.get('X-RateLimit-Limit') || '') || undefined;
  const windowSec = Number(h.get('X-RateLimit-Window') || '') || undefined;
  const remaining = Number(h.get('X-RateLimit-Remaining') || '') || undefined;
  const reset = Number(h.get('X-RateLimit-Reset') || '') || undefined;
  const retry = Number(h.get('Retry-After') || '') || undefined;
  return { limit, window: windowSec, remaining, reset, retry_after: retry };
}

function normalizeError(res: Response | null, body: unknown): ApiError {
  const status = res ? res.status : 0;
  const rl: RateLimitMeta = res ? parseRateLimitHeaders(res) : {};
  let detail = res?.statusText?.trim() || 'Request failed';

  if (body && typeof body === 'object') {
    const record = body as Record<string, unknown>;
    const rawDetail = record.detail ?? record.message;
    if (typeof rawDetail === 'string' && rawDetail.trim()) {
      detail = rawDetail;
    } else if (Array.isArray(rawDetail)) {
      detail = rawDetail.map((entry) => String(entry)).join(', ');
    }
  }

  if (status === 401 && detail === (res?.statusText || detail)) {
    detail = 'Authorization required';
  }
  if (status === 403 && detail === (res?.statusText || detail)) {
    detail = 'Insufficient permissions';
  }
  if (status === 429) {
    const sec = rl.retry_after || rl.reset;
    if (sec) detail = `Too many requests. Retry after ${sec}s`;
  }
  return {
    status,
    detail,
    error_code:
      body && typeof body === 'object' && 'error_code' in body && typeof (body as Record<string, unknown>).error_code === 'string'
        ? (body as Record<string, string>).error_code
        : undefined,
    retry_after: rl.retry_after,
    rate_limit: { limit: rl.limit, window: rl.window, remaining: rl.remaining, reset: rl.reset },
    raw: body,
  };
}

function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    typeof (value as { status: unknown }).status === 'number' &&
    'detail' in value &&
    typeof (value as { detail: unknown }).detail === 'string'
  );
}

async function http<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    const res = await fetch(withBase(path), options);
    if (!res.ok) {
      // Try to extract JSON error
      let body: unknown;
      try {
        body = await res.json();
      } catch {
        try {
          body = { detail: await res.text() };
        } catch {
          body = {};
        }
      }
      const err = normalizeError(res, body);
      throw err;
    }
    if (res.status === 204) {
      return undefined as T;
    }
    const contentType = res.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      return (await res.json()) as T;
    }
    return undefined as T;
  } catch (e: unknown) {
    if (isApiError(e)) {
      throw e;
    }
    // Network or unexpected
    const err: ApiError = {
      status: 0,
      detail: e instanceof Error ? e.message : 'Network error',
      raw: e,
    };
    throw err;
  }
}

// Menu
export const getDailyMenu = () => http<DailyMenuResponse>('/admin/daily-menu', { headers: getAuthHeaders() });
export const replaceDailyMenu = (itemIds: number[]) =>
  http<SuccessResponse>('/admin/daily-menu/replace', {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_ids: itemIds }),
  });
export const clearDailyMenu = () =>
  http<SuccessResponse>('/admin/daily-menu/clear', {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
export const getDailyMenuDate = () => http<MenuDateResponse>('/admin/daily-menu/date', { headers: getAuthHeaders() });
export const setDailyMenuDate = (payload: { start_date: string; end_date: string }) =>
  http<SuccessResponse>('/admin/daily-menu/date', {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

// Items
export const getItems = async (): Promise<Item[]> => {
  const data = await http<ItemListResponse>('/admin/items', { headers: getAuthHeaders() });
  return data.items;
};
export const getItem = (id: number) => http<Item>(`/admin/items/${id}`, { headers: getAuthHeaders() });
export const createItem = (payload: Record<string, unknown>) =>
  http<SuccessResponse>('/admin/items', {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
export const updateItem = (id: number, payload: Record<string, unknown>) =>
  http<SuccessResponse>(`/admin/items/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
export const deleteItem = (id: number) =>
  http<SuccessResponse>(`/admin/items/${id}`, { method: 'DELETE', headers: getAuthHeaders() });
export const getItemsOrphaned = async (): Promise<Item[]> => {
  const data = await http<ItemListResponse>('/admin/items/orphaned', {
    headers: getAuthHeaders(),
  });
  return data.items;
};
export const getItemsNoUnit = async (): Promise<Item[]> => {
  const data = await http<ItemListResponse>('/admin/items/no-unit', {
    headers: getAuthHeaders(),
  });
  return data.items;
};
export const moveOrphanedToCategory = (categoryId: number, itemIds: number[]) =>
  http<SuccessResponse>(`/admin/categories/${categoryId}/move-orphaned`, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_ids: itemIds }),
  });
export const moveNoUnitToUnit = (unitId: number, itemIds: number[]) =>
  http<SuccessResponse>(`/admin/units/${unitId}/move-no-unit`, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_ids: itemIds }),
  });

// Categories
export const getCategories = async (): Promise<Category[]> => {
  const data = await http<CategoryListResponse>('/admin/categories', {
    headers: getAuthHeaders(),
  });
  return data.categories;
};
export const createCategory = (title: string) =>
  http<SuccessResponse>('/admin/categories', {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
export const updateCategory = (id: number, title: string) =>
  http<SuccessResponse>(`/admin/categories/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
export const deleteCategory = (id: number, keepItems: boolean) =>
  http<SuccessResponse>(`/admin/categories/${id}?keep_items=${keepItems}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
export const moveCategoryUp = (id: number) =>
  http<SuccessResponse>(`/admin/categories/${id}/move-up`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
export const moveCategoryDown = (id: number) =>
  http<SuccessResponse>(`/admin/categories/${id}/move-down`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

// Units
export const getUnits = async (): Promise<Unit[]> => {
  const data = await http<UnitListResponse>('/admin/units', { headers: getAuthHeaders() });
  return data.units;
};
export const createUnit = (name: string) =>
  http<SuccessResponse>('/admin/units', {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
export const updateUnit = (id: number, name: string) =>
  http<SuccessResponse>(`/admin/units/${id}`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
export const deleteUnit = (id: number, keepItems: boolean) =>
  http<SuccessResponse>(`/admin/units/${id}?keep_items=${keepItems}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
export const moveUnitUp = (id: number) =>
  http<SuccessResponse>(`/admin/units/${id}/move-up`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
export const moveUnitDown = (id: number) =>
  http<SuccessResponse>(`/admin/units/${id}/move-down`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

// Images
export const getImages = async (): Promise<AppImage[]> => {
  const data = await http<ImageListResponse>('/admin/images', { headers: getAuthHeaders() });
  return data.images;
};
export const uploadImage = async (file: File): Promise<AppImage> => {
  const formData = new FormData();
  formData.append('file', file);
  return http<AppImage>('/admin/images/upload', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
};
export const deleteImage = (imageId: number) =>
  http<SuccessResponse>(`/admin/images/${imageId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
