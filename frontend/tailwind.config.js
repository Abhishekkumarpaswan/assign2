/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#E6F7F4',
          100: '#CCF0E9',
          200: '#99E1D3',
          300: '#66D1BD',
          400: '#33C2A7',
          500: '#03AB8F', // Exact user brand teal
          600: '#028D76',
          700: '#026E5C',
          800: '#014F42',
          900: '#013028',
        },
        slate: {
          50: '#F8FAFC',
          100: '#F1F5F9', // Exact user slate background
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
        },
        muted: '#8E8E93', // User muted gray
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
