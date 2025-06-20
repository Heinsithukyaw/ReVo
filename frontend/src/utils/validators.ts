// Basic validation functions
export const isRequired = (value: any): boolean => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  return true;
};

export const isEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isURL = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isValidJSON = (jsonString: string): boolean => {
  try {
    JSON.parse(jsonString);
    return true;
  } catch {
    return false;
  }
};

// String validators
export const minLength = (value: string, min: number): boolean => {
  return value.length >= min;
};

export const maxLength = (value: string, max: number): boolean => {
  return value.length <= max;
};

export const isAlphanumeric = (value: string): boolean => {
  const alphanumericRegex = /^[a-zA-Z0-9]+$/;
  return alphanumericRegex.test(value);
};

export const isNumeric = (value: string): boolean => {
  return !isNaN(Number(value)) && !isNaN(parseFloat(value));
};

// Number validators
export const isPositiveNumber = (value: number): boolean => {
  return typeof value === 'number' && value > 0;
};

export const isInRange = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max;
};

export const isInteger = (value: number): boolean => {
  return Number.isInteger(value);
};

// Agent-specific validators
export const isValidAgentName = (name: string): boolean => {
  return isRequired(name) && minLength(name, 2) && maxLength(name, 50);
};

export const isValidAgentType = (type: string): boolean => {
  const validTypes = ['code', 'workflow', 'knowledge', 'integration'];
  return validTypes.includes(type);
};

export const isValidAgentStatus = (status: string): boolean => {
  const validStatuses = ['active', 'inactive', 'busy', 'error'];
  return validStatuses.includes(status);
};

// Chat validators
export const isValidMessage = (message: string): boolean => {
  return isRequired(message) && maxLength(message, 5000);
};

export const isValidSessionTitle = (title: string): boolean => {
  return isRequired(title) && minLength(title, 1) && maxLength(title, 100);
};

// File validators
export const isValidFileSize = (file: File, maxSizeInMB: number): boolean => {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return file.size <= maxSizeInBytes;
};

export const isValidFileType = (file: File, allowedTypes: string[]): boolean => {
  return allowedTypes.includes(file.type);
};

export const isImageFile = (file: File): boolean => {
  return file.type.startsWith('image/');
};

export const isCodeFile = (filename: string): boolean => {
  const codeExtensions = [
    '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.cs',
    '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
    '.html', '.css', '.scss', '.less', '.json', '.xml', '.yaml', '.yml'
  ];
  
  return codeExtensions.some(ext => filename.toLowerCase().endsWith(ext));
};

// Configuration validators
export const isValidPort = (port: number): boolean => {
  return isInteger(port) && isInRange(port, 1, 65535);
};

export const isValidTimeout = (timeout: number): boolean => {
  return isPositiveNumber(timeout) && timeout <= 300000; // Max 5 minutes
};

export const isValidRetryCount = (retries: number): boolean => {
  return isInteger(retries) && isInRange(retries, 0, 10);
};

// System validators
export const isValidCPUUsage = (usage: number): boolean => {
  return isInRange(usage, 0, 100);
};

export const isValidMemoryUsage = (usage: number): boolean => {
  return isInRange(usage, 0, 100);
};

export const isValidPercentage = (value: number): boolean => {
  return isInRange(value, 0, 100);
};

// API validators
export const isValidAPIKey = (apiKey: string): boolean => {
  return isRequired(apiKey) && minLength(apiKey, 10);
};

export const isValidEndpoint = (endpoint: string): boolean => {
  return isRequired(endpoint) && endpoint.startsWith('/');
};

// Validation result type
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Comprehensive validator functions
export const validateAgent = (agent: any): ValidationResult => {
  const errors: string[] = [];

  if (!isValidAgentName(agent.name)) {
    errors.push('Agent name must be between 2 and 50 characters');
  }

  if (!isValidAgentType(agent.type)) {
    errors.push('Agent type must be one of: code, workflow, knowledge, integration');
  }

  if (!isValidAgentStatus(agent.status)) {
    errors.push('Agent status must be one of: active, inactive, busy, error');
  }

  if (!isRequired(agent.description)) {
    errors.push('Agent description is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateChatMessage = (message: any): ValidationResult => {
  const errors: string[] = [];

  if (!isValidMessage(message.content)) {
    errors.push('Message content is required and must be less than 5000 characters');
  }

  if (!isRequired(message.role)) {
    errors.push('Message role is required');
  }

  if (!['user', 'assistant', 'system'].includes(message.role)) {
    errors.push('Message role must be user, assistant, or system');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateSystemMetrics = (metrics: any): ValidationResult => {
  const errors: string[] = [];

  if (!isValidCPUUsage(metrics.cpuUsage)) {
    errors.push('CPU usage must be between 0 and 100');
  }

  if (!isValidMemoryUsage(metrics.memoryUsage)) {
    errors.push('Memory usage must be between 0 and 100');
  }

  if (!isValidPercentage(metrics.diskUsage)) {
    errors.push('Disk usage must be between 0 and 100');
  }

  if (!isRequired(metrics.timestamp)) {
    errors.push('Timestamp is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};