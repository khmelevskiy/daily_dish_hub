import { useEffect, useState, useMemo } from 'react';
import { DEFAULTS, type AppPublicSettings, loadAppSettings, getCachedSettings, formatPriceWithIntl } from '../config';

export default function useSettings() {
  const [settings, setSettings] = useState<AppPublicSettings>(getCachedSettings() || DEFAULTS);

  useEffect(() => {
    void loadAppSettings().then(setSettings);
  }, []);

  const formatPrice = useMemo(() => {
    return (amount: number | string): string => formatPriceWithIntl(amount, settings);
  }, [settings]);

  return { ...settings, formatPrice };
}
