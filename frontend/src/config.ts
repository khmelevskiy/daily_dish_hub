// Centralized application public settings and price formatter
import { withBase } from './services/config';
export type AppPublicSettings = {
  site_name: string;
  site_description: string;
  currency_code: string; // ISO 4217
  currency_symbol: string; // Display symbol fallback
  currency_locale: string; // BCP 47 locale
};

export const DEFAULTS: AppPublicSettings = {
  site_name: 'Canteen Menu',
  site_description: 'Fresh and tasty dishes every day',
  currency_code: 'GEL',
  currency_symbol: '₾',
  currency_locale: 'en-GE',
};

let cachedSettings: AppPublicSettings | null = null;
let inFlight: Promise<AppPublicSettings> | null = null;

export async function loadAppSettings(): Promise<AppPublicSettings> {
  if (cachedSettings) return cachedSettings;
  if (inFlight) return inFlight;
  inFlight = fetch(withBase('/public/settings'))
    .then((res) => (res.ok ? res.json() : DEFAULTS))
    .then((data) => ({ ...DEFAULTS, ...(data || {}) }))
    .catch(() => DEFAULTS)
    .then((settings) => {
      cachedSettings = settings;
      inFlight = null;
      return settings;
    });
  return inFlight;
}

export function getCachedSettings(): AppPublicSettings {
  return cachedSettings || DEFAULTS;
}

export function formatPriceWithIntl(
  amount: number | string,
  settings: AppPublicSettings = getCachedSettings()
): string {
  const n = typeof amount === 'number' ? amount : parseFloat(String(amount) || '0');
  const safeN = Number.isFinite(n) ? n : 0;

  // Use Intl to discover currency part and ensure 2 fraction digits.
  try {
    const nf = new Intl.NumberFormat(settings.currency_locale || 'en-US', {
      style: 'currency',
      currency: settings.currency_code || 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

    // We still want to preserve UI layout "123.45 SYMBOL".
    // Use formatToParts to extract currency sign (or fallback), but build number with dot separator.
    const parts = nf.formatToParts(safeN);
    const symbolPart = parts.find((p) => p.type === 'currency');
    const sym = symbolPart?.value || settings.currency_symbol || '$';

    // Build canonical number with dot decimal to match existing UI.
    const numStr = safeN.toFixed(2);
    return `${numStr} ${sym}`;
  } catch {
    // Fallback: strict legacy format
    return `${safeN.toFixed(2)} ${settings.currency_symbol || '$'}`;
  }
}
