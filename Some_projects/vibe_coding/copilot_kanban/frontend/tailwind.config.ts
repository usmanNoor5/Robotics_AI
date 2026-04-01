import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        accent: '#ecad0a',
        primary: '#209dd7',
        secondary: '#753991',
        darknavy: '#032147',
        graytext: '#888888',
      },
    },
  },
  plugins: [],
};

export default config;
