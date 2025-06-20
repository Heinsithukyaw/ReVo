// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:12001',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// WebSocket Configuration
export const WS_CONFIG = {
  BASE_URL: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:12001',
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY: 3000,
  HEARTBEAT_INTERVAL: 30000,
} as const;

// Application Routes
export const ROUTES = {
  HOME: '/',
  OVERVIEW: '/',
  AGENTS: '/agents',
  CHAT: '/chat',
  ANALYTICS: '/analytics',
} as const;

// Agent Types
export const AGENT_TYPES = {
  CODE: 'code',
  WORKFLOW: 'workflow',
  KNOWLEDGE: 'knowledge',
  INTEGRATION: 'integration',
} as const;

// Agent Statuses
export const AGENT_STATUSES = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  BUSY: 'busy',
  ERROR: 'error',
} as const;

// Task Statuses
export const TASK_STATUSES = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

// Message Roles
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
} as const;

// Session Statuses
export const SESSION_STATUSES = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
} as const;

// Engine Names
export const ENGINE_NAMES = {
  MEMORY: 'Perfect Recall Engine',
  PARALLEL: 'Parallel Mind Engine',
  CREATIVE: 'Creative Engine',
} as const;

// Engine Statuses
export const ENGINE_STATUSES = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  ERROR: 'error',
} as const;

// Notification Types
export const NOTIFICATION_TYPES = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  SUCCESS: 'success',
} as const;

// File Types
export const FILE_TYPES = {
  IMAGE: 'image',
  CODE: 'code',
  DOCUMENT: 'document',
  ARCHIVE: 'archive',
} as const;

// Supported File Extensions
export const SUPPORTED_FILE_EXTENSIONS = {
  IMAGES: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
  CODE: ['.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go'],
  DOCUMENTS: ['.txt', '.md', '.pdf', '.doc', '.docx'],
  ARCHIVES: ['.zip', '.tar', '.gz', '.rar'],
} as const;

// Time Ranges for Analytics
export const TIME_RANGES = {
  HOUR: '1h',
  DAY: '24h',
  WEEK: '7d',
  MONTH: '30d',
  QUARTER: '90d',
  YEAR: '365d',
} as const;

// Refresh Intervals (in milliseconds)
export const REFRESH_INTERVALS = {
  FAST: 1000,
  NORMAL: 5000,
  SLOW: 10000,
  VERY_SLOW: 30000,
} as const;

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  CHAT_MESSAGE_LIMIT: 50,
} as const;

// UI Constants
export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 320,
  HEADER_HEIGHT: 64,
  FOOTER_HEIGHT: 48,
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024,
  DESKTOP_BREAKPOINT: 1280,
} as const;

// Animation Durations (in milliseconds)
export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  VERY_SLOW: 1000,
} as const;

// Colors
export const COLORS = {
  PRIMARY: '#3B82F6',
  SECONDARY: '#8B5CF6',
  SUCCESS: '#10B981',
  WARNING: '#F59E0B',
  ERROR: '#EF4444',
  INFO: '#06B6D4',
} as const;

// Status Colors
export const STATUS_COLORS = {
  ACTIVE: '#10B981',
  INACTIVE: '#6B7280',
  BUSY: '#F59E0B',
  ERROR: '#EF4444',
  SUCCESS: '#10B981',
  WARNING: '#F59E0B',
  INFO: '#06B6D4',
} as const;

// Agent Categories
export const AGENT_CATEGORIES = {
  CODE_TEAM: {
    id: 'code',
    title: 'Code Team Agents',
    color: 'blue',
    description: 'Agents specialized in software development',
  },
  WORKFLOW: {
    id: 'workflow',
    title: 'Workflow Management',
    color: 'purple',
    description: 'Agents managing processes and workflows',
  },
  KNOWLEDGE: {
    id: 'knowledge',
    title: 'Knowledge & Memory',
    color: 'green',
    description: 'Agents handling knowledge and memory systems',
  },
  INTEGRATION: {
    id: 'integration',
    title: 'Integration & Communication',
    color: 'orange',
    description: 'Agents managing external integrations',
  },
} as const;

// System Metrics Thresholds
export const METRICS_THRESHOLDS = {
  CPU: {
    LOW: 30,
    MEDIUM: 70,
    HIGH: 90,
  },
  MEMORY: {
    LOW: 40,
    MEDIUM: 75,
    HIGH: 90,
  },
  DISK: {
    LOW: 50,
    MEDIUM: 80,
    HIGH: 95,
  },
  RESPONSE_TIME: {
    GOOD: 1000,
    ACCEPTABLE: 3000,
    POOR: 5000,
  },
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  GENERIC: 'An unexpected error occurred. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  TIMEOUT: 'Request timeout. Please try again.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  AGENT_CREATED: 'Agent created successfully',
  AGENT_UPDATED: 'Agent updated successfully',
  AGENT_DELETED: 'Agent deleted successfully',
  MESSAGE_SENT: 'Message sent successfully',
  SESSION_CREATED: 'Session created successfully',
  TASK_COMPLETED: 'Task completed successfully',
  SETTINGS_SAVED: 'Settings saved successfully',
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  USER_PREFERENCES: 'revoagent_user_preferences',
  CHAT_HISTORY: 'revoagent_chat_history',
  AGENT_CONFIGURATIONS: 'revoagent_agent_configs',
  DASHBOARD_LAYOUT: 'revoagent_dashboard_layout',
  THEME_SETTINGS: 'revoagent_theme_settings',
} as const;

// Feature Flags
export const FEATURE_FLAGS = {
  ENABLE_VOICE_INPUT: import.meta.env.VITE_ENABLE_VOICE_INPUT === 'true',
  ENABLE_FILE_UPLOAD: import.meta.env.VITE_ENABLE_FILE_UPLOAD === 'true',
  ENABLE_REAL_TIME: import.meta.env.VITE_ENABLE_REAL_TIME === 'true',
  ENABLE_ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  ENABLE_NOTIFICATIONS: import.meta.env.VITE_ENABLE_NOTIFICATIONS === 'true',
} as const;

// Development Constants
export const DEV_CONFIG = {
  MOCK_DELAY: 1000,
  ENABLE_MOCK_DATA: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
  ENABLE_DEBUG_LOGS: import.meta.env.VITE_ENABLE_DEBUG_LOGS === 'true',
} as const;