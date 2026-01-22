/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Rwanda Flag Colors
        primary: {
          DEFAULT: '#00A1DE',
          light: '#E6F4FB',
          dark: '#0077A8',
        },
        secondary: {
          DEFAULT: '#20603D',
          light: '#E8F5E9',
          dark: '#1A4D31',
        },
        accent: {
          DEFAULT: '#FAD201',
          light: '#FFF9E6',
          dark: '#C9A801',
        },
        // Semantic colors
        success: '#20603D',
        warning: '#FAD201',
        error: '#DC3545',
        info: '#00A1DE',
        // Neutrals
        background: '#F5F9FC',
        surface: '#FFFFFF',
        text: {
          DEFAULT: '#1A1A1A',
          muted: '#6B7280',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        korean: ['Noto Sans KR', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.06)',
        'medium': '0 4px 16px rgba(0, 0, 0, 0.1)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
      },
    },
  },
  plugins: [],
}
