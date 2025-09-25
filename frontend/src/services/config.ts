// Resolve API base URL from environment (Vite only)
function getEnvApiBase(): string | undefined {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const v = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
    if (v && typeof v === 'string') return v;
  } catch {}
  return undefined;
}

function normalizeBase(u?: string): string {
  const s = (u || '').trim();
  if (!s) return '';
  // Remove trailing slash for consistent joining
  return s.endsWith('/') ? s.slice(0, -1) : s;
}

export const API_BASE: string = normalizeBase(getEnvApiBase() || '');

export const withBase = (path: string): string => {
  if (!API_BASE) return path;
  if (!path) return API_BASE;
  // Ensure single slash between base and path
  return path.startsWith('/') ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
};
