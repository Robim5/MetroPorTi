// guarda e le o url da api e a api key no browser
export const STORAGE_BASE = "metroporti_api_base";
export const STORAGE_KEY = "metroporti_api_key";

export function getApiBase() {
  const saved = localStorage.getItem(STORAGE_BASE);
  if (saved) return saved.replace(/\/$/, "");
  return window.location.origin;
}

export function getApiKey() {
  return localStorage.getItem(STORAGE_KEY) || "";
}

export function saveSettings(base, key) {
  localStorage.setItem(STORAGE_BASE, base.replace(/\/$/, ""));
  localStorage.setItem(STORAGE_KEY, key);
}
