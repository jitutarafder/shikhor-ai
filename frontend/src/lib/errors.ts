/**
 * Unified error extraction and formatting utility.
 * Safely extracts user-facing error messages from API responses, Error objects, or unknown thrown values.
 */
export function getErrorMessage(err: unknown, defaultMessage = "একটি অপ্রত্যাশিত ত্রুটি ঘটেছে।"): string {
  if (!err) return defaultMessage;
  if (typeof err === "string") return err;
  if (err instanceof Error) {
    if (err.name === "TypeError" || err.message?.includes("fetch") || err.message?.includes("NetworkError")) {
      return "সার্ভারের সাথে সংযোগ স্থাপন করা যায়নি (নেটওয়ার্ক সমস্যা বা সার্ভার বন্ধ)।";
    }
    return err.message || defaultMessage;
  }
  if (typeof err === "object") {
    const obj = err as Record<string, unknown>;
    if (typeof obj.message === "string" && obj.message) return obj.message;
    if (typeof obj.detail === "string" && obj.detail) return obj.detail;
    if (obj.error && typeof obj.error === "object") {
      const nested = obj.error as Record<string, unknown>;
      if (typeof nested.message === "string" && nested.message) return nested.message;
    }
  }
  return defaultMessage;
}
