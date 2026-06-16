// runtime-flags.ts — small browser-runtime feature flags shared by the Atlas UI.

const truthy = (value: unknown): boolean => {
  if (value === true) return true;
  const text = String(value ?? '').trim().toLowerCase();
  return ['1', 'true', 'yes', 'on', 'enable', 'enabled'].includes(text);
};

export const atlasOagMode = (): boolean => {
  try {
    const w = window as any;
    const boot = w.ATLAS_BOOT_CONFIG || {};
    if (Object.prototype.hasOwnProperty.call(boot, 'oag_mode')) {
      return truthy(boot.oag_mode);
    }
    if (Object.prototype.hasOwnProperty.call(boot, 'oagMode')) {
      return truthy(boot.oagMode);
    }
    return truthy(w.OAG_MODE);
  } catch (_) {
    return false;
  }
};
