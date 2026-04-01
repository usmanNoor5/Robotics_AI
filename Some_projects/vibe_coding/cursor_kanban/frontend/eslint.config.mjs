import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

// Next.js ships ESLint configs as "legacy" presets (extends-style).
// With ESLint 9 flat config, we adapt them via FlatCompat.
const compat = new FlatCompat({
  baseDirectory: dirname(fileURLToPath(import.meta.url)),
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
      // Keep generated artifacts out of lint.
      ".cursor/**",
    ],
  },
];

export default eslintConfig;
