import ko from "./ko.json";
import en from "./en.json";

export type Language = "ko" | "en";

export const translations = {
  ko,
  en,
} as const;

// Type-safe translation keys
export type TranslationKey = keyof typeof ko | string;
