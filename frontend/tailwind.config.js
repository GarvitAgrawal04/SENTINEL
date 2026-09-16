/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: '#03050D',
        obsidian: {
          950: '#04060E',
          900: '#070B19',
          850: '#0B1126',
          800: '#0F1734',
          700: '#162248',
          600: '#1E2E60',
        },
        cyber: {
          300: '#5EEAD4',
          400: '#2DD4BF',
          DEFAULT: '#00F5A0',
          500: '#00E599',
          600: '#059669',
        },
        hologram: {
          300: '#7DD3FC',
          400: '#38BDF8',
          DEFAULT: '#00F2FE',
          500: '#0EA5E9',
          600: '#0284C7',
        },
        nebula: {
          300: '#D8B4FE',
          400: '#C084FC',
          DEFAULT: '#9333EA',
          500: '#7928CA',
          600: '#7E22CE',
        },
        supernova: {
          300: '#FDA4AF',
          400: '#FB7185',
          DEFAULT: '#FF0055',
          500: '#FF2E63',
          600: '#E11D48',
        },
        caution: {
          300: '#FDE68A',
          400: '#FBBF24',
          DEFAULT: '#F59E0B',
          500: '#D97706',
        },
        terminal: '#00E599',
        threat: '#FF2E63',
        suspicious: '#F59E0B',
      },
      fontFamily: {
        sans: ['Space Grotesk', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['Space Mono', 'JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Syne', 'Space Grotesk', 'Inter', 'sans-serif'],
        syne: ['Syne', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyber': '0 0 25px -5px rgba(0, 245, 160, 0.4)',
        'glow-hologram': '0 0 25px -5px rgba(0, 242, 254, 0.4)',
        'glow-threat': '0 0 25px -5px rgba(255, 46, 99, 0.4)',
        'glow-nebula': '0 0 25px -5px rgba(121, 40, 202, 0.4)',
        'glass-edge': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.1)',
        'glass-card': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      animation: {
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
        'laser-sweep': 'laserSweep 4s linear infinite',
        'float-slow': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s infinite',
        'spin-slow': 'spin 12s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.4', filter: 'drop-shadow(0 0 15px rgba(0, 245, 160, 0.3))' },
          '50%': { opacity: '0.8', filter: 'drop-shadow(0 0 30px rgba(0, 242, 254, 0.6))' },
        },
        laserSweep: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
  plugins: [],
}
