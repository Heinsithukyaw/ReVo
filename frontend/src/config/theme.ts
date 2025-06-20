import { COLORS, STATUS_COLORS, ANIMATION_DURATIONS } from '../utils/constants';

// Theme Configuration
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      muted: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  animations: {
    fast: number;
    normal: number;
    slow: number;
  };
}

// Dark Theme (Default)
export const darkTheme: Theme = {
  colors: {
    primary: COLORS.PRIMARY,
    secondary: COLORS.SECONDARY,
    success: COLORS.SUCCESS,
    warning: COLORS.WARNING,
    error: COLORS.ERROR,
    info: COLORS.INFO,
    background: '#0F172A',
    surface: '#1E293B',
    text: {
      primary: '#F8FAFC',
      secondary: '#CBD5E1',
      muted: '#64748B',
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  },
  animations: {
    fast: ANIMATION_DURATIONS.FAST,
    normal: ANIMATION_DURATIONS.NORMAL,
    slow: ANIMATION_DURATIONS.SLOW,
  },
};

// Light Theme
export const lightTheme: Theme = {
  ...darkTheme,
  colors: {
    ...darkTheme.colors,
    background: '#FFFFFF',
    surface: '#F8FAFC',
    text: {
      primary: '#0F172A',
      secondary: '#475569',
      muted: '#94A3B8',
    },
  },
};

// Status Theme Colors
export const statusTheme = {
  active: STATUS_COLORS.ACTIVE,
  inactive: STATUS_COLORS.INACTIVE,
  busy: STATUS_COLORS.BUSY,
  error: STATUS_COLORS.ERROR,
  success: STATUS_COLORS.SUCCESS,
  warning: STATUS_COLORS.WARNING,
  info: STATUS_COLORS.INFO,
};

// Agent Category Colors
export const agentCategoryColors = {
  code: {
    primary: '#3B82F6',
    background: 'rgba(59, 130, 246, 0.1)',
    border: 'rgba(59, 130, 246, 0.3)',
  },
  workflow: {
    primary: '#8B5CF6',
    background: 'rgba(139, 92, 246, 0.1)',
    border: 'rgba(139, 92, 246, 0.3)',
  },
  knowledge: {
    primary: '#10B981',
    background: 'rgba(16, 185, 129, 0.1)',
    border: 'rgba(16, 185, 129, 0.3)',
  },
  integration: {
    primary: '#F59E0B',
    background: 'rgba(245, 158, 11, 0.1)',
    border: 'rgba(245, 158, 11, 0.3)',
  },
};

// Glassmorphism Theme
export const glassmorphismTheme = {
  background: 'rgba(255, 255, 255, 0.1)',
  backdrop: 'blur(16px)',
  border: 'rgba(255, 255, 255, 0.2)',
  shadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
};

// Typography Scale
export const typography = {
  fontSizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  fontWeights: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeights: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
};

// Breakpoints for Responsive Design
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// Z-Index Scale
export const zIndex = {
  base: 1,
  dropdown: 10,
  modal: 50,
  popover: 100,
  tooltip: 200,
  notification: 300,
};

// Custom CSS Variables for Dynamic Theming
export const cssVariables = {
  '--color-primary': darkTheme.colors.primary,
  '--color-secondary': darkTheme.colors.secondary,
  '--color-success': darkTheme.colors.success,
  '--color-warning': darkTheme.colors.warning,
  '--color-error': darkTheme.colors.error,
  '--color-info': darkTheme.colors.info,
  '--color-background': darkTheme.colors.background,
  '--color-surface': darkTheme.colors.surface,
  '--color-text-primary': darkTheme.colors.text.primary,
  '--color-text-secondary': darkTheme.colors.text.secondary,
  '--color-text-muted': darkTheme.colors.text.muted,
  '--border-radius-sm': darkTheme.borderRadius.sm,
  '--border-radius-md': darkTheme.borderRadius.md,
  '--border-radius-lg': darkTheme.borderRadius.lg,
  '--border-radius-xl': darkTheme.borderRadius.xl,
  '--spacing-xs': darkTheme.spacing.xs,
  '--spacing-sm': darkTheme.spacing.sm,
  '--spacing-md': darkTheme.spacing.md,
  '--spacing-lg': darkTheme.spacing.lg,
  '--spacing-xl': darkTheme.spacing.xl,
};

// Theme Context Helper
export const getThemeValue = (path: string, theme: Theme = darkTheme): any => {
  return path.split('.').reduce((obj, key) => obj?.[key], theme);
};

// Default Export
export const theme = darkTheme;