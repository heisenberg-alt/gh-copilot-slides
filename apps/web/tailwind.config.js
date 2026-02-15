/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Apple-inspired color palette
      colors: {
        background: 'var(--background)',
        surface: 'var(--surface)',
        'surface-elevated': 'var(--surface-elevated)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        accent: 'var(--accent)',
        'accent-hover': 'var(--accent-hover)',
        border: 'var(--border)',

        // Semantic colors
        success: '#34C759',
        warning: '#FF9500',
        error: '#FF3B30',
        info: '#5AC8FA',
      },

      // Apple-inspired typography
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: [
          'SF Mono',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
      },

      // Apple-inspired spacing (8px grid)
      spacing: {
        '4.5': '1.125rem', // 18px
        '13': '3.25rem',   // 52px
        '15': '3.75rem',   // 60px
        '18': '4.5rem',    // 72px
        '22': '5.5rem',    // 88px
      },

      // Apple-inspired border radius
      borderRadius: {
        'apple': '12px',
        'apple-lg': '16px',
        'apple-xl': '20px',
        'apple-2xl': '24px',
      },

      // Apple-inspired shadows
      boxShadow: {
        'apple-sm': '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'apple': '0 2px 8px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.04)',
        'apple-lg': '0 4px 12px rgba(0, 0, 0, 0.08), 0 8px 32px rgba(0, 0, 0, 0.08)',
        'apple-elevated': '0 8px 28px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08)',
      },

      // Apple-inspired animations
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'fade-up': 'fadeUp 0.4s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },

      // Transitions
      transitionDuration: {
        '250': '250ms',
        '350': '350ms',
      },
      transitionTimingFunction: {
        'apple': 'cubic-bezier(0.25, 0.1, 0.25, 1)',
        'apple-spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      },
    },
  },
  plugins: [],
};
