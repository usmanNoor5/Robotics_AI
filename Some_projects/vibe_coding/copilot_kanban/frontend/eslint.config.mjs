import { defineConfig } from "eslint/config";

const eslintConfig = defineConfig({
  extends: ["next", "next/core-web-vitals", "next/typescript"],
  ignorePatterns: [".next/**", "out/**", "build/**", "next-env.d.ts"],
});

export default eslintConfig;
