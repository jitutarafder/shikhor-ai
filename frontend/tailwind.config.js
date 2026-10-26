/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          900: '#153D2C',
          700: '#216245',
        },
        leaf: {
          500: '#42A66A',
          100: '#E7F5EC',
        },
        paddy: {
          400: '#D7B84A',
        },
        sun: {
          300: '#F2CC67',
        },
        soil: {
          700: '#76543B',
          100: '#F5EEE7',
        },
        sky: {
          600: '#2878A7',
        },
        danger: {
          600: '#C9463D',
        },
        ink: {
          900: '#17211B',
          600: '#5D685F',
        },
        line: {
          200: '#DDE6DF',
        },
        canvas: '#FFFFFF',
        surface: '#F7FAF7',
      },
      fontFamily: {
        bengali: ['"Noto Sans Bengali"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['Inter', '"Noto Sans Bengali"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '16px',
        btn: '12px',
      },
      boxShadow: {
        soft: '0 1px 2px rgba(21, 61, 44, .05), 0 12px 32px rgba(21, 61, 44, .08)',
      },
    },
  },
  plugins: [],
};
