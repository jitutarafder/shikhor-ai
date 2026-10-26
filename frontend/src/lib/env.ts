import { z } from "zod";

/**
 * Runtime schema validation for Vite frontend environment variables.
 * Enforces safe fail-fast defaults during startup.
 */
const envSchema = z.object({
  VITE_APP_TITLE: z.string().default("Shikhor AI"),
  VITE_API_BASE_URL: z.string().url().default("http://localhost:8000/api/v1"),
  VITE_DEFAULT_LOCALE: z.enum(["bn", "en"]).default("bn"),
  VITE_FIREBASE_API_KEY: z.string().optional(),
  VITE_FIREBASE_AUTH_DOMAIN: z.string().optional(),
  VITE_FIREBASE_PROJECT_ID: z.string().optional(),
  VITE_FIREBASE_STORAGE_BUCKET: z.string().optional(),
  VITE_FIREBASE_MESSAGING_SENDER_ID: z.string().optional(),
  VITE_FIREBASE_APP_ID: z.string().optional(),
});

const parsed = envSchema.safeParse(import.meta.env);

if (!parsed.success) {
  console.error("❌ Invalid environment variables:", parsed.error.flatten().fieldErrors);
  throw new Error("Invalid frontend environment variables. Check .env file.");
}

export const env = parsed.data;
