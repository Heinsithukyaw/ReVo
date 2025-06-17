// Agent Categories and Definitions for Multi-Agent Workspace Arena
export interface Agent {
  id: string;
  name: string;
  icon: string;
  description: string;
  capabilities: string[];
  category: string;
  color: string;
  engineType: 'memory' | 'parallel' | 'creative' | 'hybrid';
}

export interface AgentCategory {
  id: string;
  name: string;
  icon: string;
  agents: Agent[];
}

export const AGENT_CATEGORIES: AgentCategory[] = [
  {
    id: 'development',
    name: 'Development & Engineering',
    icon: '💻',
    agents: [
      {
        id: 'fullstack-dev',
        name: 'FullStack Dev',
        icon: '🚀',
        description: 'Complete web application development with modern frameworks',
        capabilities: ['React/Vue/Angular', 'Node.js/Python/Go', 'Database Design', 'API Development'],
        category: 'development',
        color: '#3B82F6',
        engineType: 'parallel'
      },
      {
        id: 'backend-architect',
        name: 'Backend Architect',
        icon: '🏗️',
        description: 'Scalable backend systems and microservices architecture',
        capabilities: ['System Design', 'Microservices', 'Database Optimization', 'Performance Tuning'],
        category: 'development',
        color: '#8B5CF6',
        engineType: 'memory'
      },
      {
        id: 'frontend-specialist',
        name: 'Frontend Specialist',
        icon: '🎨',
        description: 'Modern UI/UX development with cutting-edge frameworks',
        capabilities: ['React/Next.js', 'TypeScript', 'Tailwind CSS', 'Component Libraries'],
        category: 'development',
        color: '#06B6D4',
        engineType: 'creative'
      },
      {
        id: 'devops-engineer',
        name: 'DevOps Engineer',
        icon: '⚙️',
        description: 'CI/CD, containerization, and cloud infrastructure',
        capabilities: ['Docker/Kubernetes', 'AWS/GCP/Azure', 'CI/CD Pipelines', 'Infrastructure as Code'],
        category: 'development',
        color: '#10B981',
        engineType: 'parallel'
      },
      {
        id: 'mobile-dev',
        name: 'Mobile Developer',
        icon: '📱',
        description: 'Cross-platform mobile app development',
        capabilities: ['React Native', 'Flutter', 'iOS/Android', 'App Store Deployment'],
        category: 'development',
        color: '#F59E0B',
        engineType: 'hybrid'
      }
    ]
  },
  {
    id: 'ai-ml',
    name: 'AI & Machine Learning',
    icon: '🧠',
    agents: [
      {
        id: 'ml-engineer',
        name: 'ML Engineer',
        icon: '🤖',
        description: 'Machine learning model development and deployment',
        capabilities: ['TensorFlow/PyTorch', 'Model Training', 'MLOps', 'Data Pipeline'],
        category: 'ai-ml',
        color: '#EF4444',
        engineType: 'memory'
      },
      {
        id: 'data-scientist',
        name: 'Data Scientist',
        icon: '📊',
        description: 'Advanced analytics and statistical modeling',
        capabilities: ['Statistical Analysis', 'Data Visualization', 'Predictive Modeling', 'A/B Testing'],
        category: 'ai-ml',
        color: '#8B5CF6',
        engineType: 'memory'
      },
      {
        id: 'nlp-specialist',
        name: 'NLP Specialist',
        icon: '💬',
        description: 'Natural language processing and understanding',
        capabilities: ['Text Analysis', 'Sentiment Analysis', 'Language Models', 'Chatbot Development'],
        category: 'ai-ml',
        color: '#06B6D4',
        engineType: 'creative'
      },
      {
        id: 'computer-vision',
        name: 'Computer Vision',
        icon: '👁️',
        description: 'Image and video analysis with deep learning',
        capabilities: ['Object Detection', 'Image Classification', 'Video Analysis', 'OCR'],
        category: 'ai-ml',
        color: '#10B981',
        engineType: 'parallel'
      }
    ]
  },
  {
    id: 'business',
    name: 'Business & Strategy',
    icon: '💼',
    agents: [
      {
        id: 'business-analyst',
        name: 'Business Analyst',
        icon: '📈',
        description: 'Requirements analysis and business process optimization',
        capabilities: ['Requirements Gathering', 'Process Mapping', 'Stakeholder Management', 'ROI Analysis'],
        category: 'business',
        color: '#3B82F6',
        engineType: 'memory'
      },
      {
        id: 'product-manager',
        name: 'Product Manager',
        icon: '🎯',
        description: 'Product strategy and roadmap development',
        capabilities: ['Product Strategy', 'Roadmap Planning', 'User Research', 'Feature Prioritization'],
        category: 'business',
        color: '#8B5CF6',
        engineType: 'hybrid'
      },
      {
        id: 'marketing-strategist',
        name: 'Marketing Strategist',
        icon: '📢',
        description: 'Digital marketing and growth strategies',
        capabilities: ['Marketing Strategy', 'Content Marketing', 'SEO/SEM', 'Social Media'],
        category: 'business',
        color: '#F59E0B',
        engineType: 'creative'
      },
      {
        id: 'financial-analyst',
        name: 'Financial Analyst',
        icon: '💰',
        description: 'Financial modeling and investment analysis',
        capabilities: ['Financial Modeling', 'Investment Analysis', 'Risk Assessment', 'Budget Planning'],
        category: 'business',
        color: '#10B981',
        engineType: 'memory'
      }
    ]
  },
  {
    id: 'creative',
    name: 'Creative & Design',
    icon: '🎨',
    agents: [
      {
        id: 'ui-designer',
        name: 'UI Designer',
        icon: '🎨',
        description: 'User interface design and visual aesthetics',
        capabilities: ['UI Design', 'Visual Design', 'Design Systems', 'Prototyping'],
        category: 'creative',
        color: '#EC4899',
        engineType: 'creative'
      },
      {
        id: 'ux-researcher',
        name: 'UX Researcher',
        icon: '🔍',
        description: 'User experience research and usability testing',
        capabilities: ['User Research', 'Usability Testing', 'Journey Mapping', 'Persona Development'],
        category: 'creative',
        color: '#8B5CF6',
        engineType: 'memory'
      },
      {
        id: 'content-creator',
        name: 'Content Creator',
        icon: '✍️',
        description: 'Creative content writing and storytelling',
        capabilities: ['Content Writing', 'Copywriting', 'Storytelling', 'Brand Voice'],
        category: 'creative',
        color: '#06B6D4',
        engineType: 'creative'
      },
      {
        id: 'graphic-designer',
        name: 'Graphic Designer',
        icon: '🖼️',
        description: 'Visual graphics and brand identity design',
        capabilities: ['Graphic Design', 'Brand Identity', 'Print Design', 'Digital Assets'],
        category: 'creative',
        color: '#F59E0B',
        engineType: 'creative'
      }
    ]
  },
  {
    id: 'security',
    name: 'Security & Compliance',
    icon: '🔒',
    agents: [
      {
        id: 'security-analyst',
        name: 'Security Analyst',
        icon: '🛡️',
        description: 'Cybersecurity analysis and threat detection',
        capabilities: ['Threat Analysis', 'Vulnerability Assessment', 'Security Auditing', 'Incident Response'],
        category: 'security',
        color: '#EF4444',
        engineType: 'parallel'
      },
      {
        id: 'compliance-officer',
        name: 'Compliance Officer',
        icon: '📋',
        description: 'Regulatory compliance and risk management',
        capabilities: ['Compliance Auditing', 'Risk Assessment', 'Policy Development', 'Regulatory Reporting'],
        category: 'security',
        color: '#8B5CF6',
        engineType: 'memory'
      },
      {
        id: 'penetration-tester',
        name: 'Penetration Tester',
        icon: '🔓',
        description: 'Ethical hacking and security testing',
        capabilities: ['Penetration Testing', 'Vulnerability Scanning', 'Security Assessment', 'Exploit Development'],
        category: 'security',
        color: '#10B981',
        engineType: 'parallel'
      }
    ]
  },
  {
    id: 'operations',
    name: 'Operations & Support',
    icon: '⚡',
    agents: [
      {
        id: 'system-admin',
        name: 'System Admin',
        icon: '🖥️',
        description: 'System administration and infrastructure management',
        capabilities: ['Server Management', 'Network Administration', 'System Monitoring', 'Backup Management'],
        category: 'operations',
        color: '#3B82F6',
        engineType: 'parallel'
      },
      {
        id: 'qa-engineer',
        name: 'QA Engineer',
        icon: '🧪',
        description: 'Quality assurance and testing automation',
        capabilities: ['Test Automation', 'Manual Testing', 'Performance Testing', 'Bug Tracking'],
        category: 'operations',
        color: '#10B981',
        engineType: 'memory'
      },
      {
        id: 'support-specialist',
        name: 'Support Specialist',
        icon: '🎧',
        description: 'Customer support and technical assistance',
        capabilities: ['Customer Support', 'Technical Documentation', 'Issue Resolution', 'User Training'],
        category: 'operations',
        color: '#F59E0B',
        engineType: 'hybrid'
      }
    ]
  }
];

// Helper functions
export const getAllAgents = (): Agent[] => {
  return AGENT_CATEGORIES.flatMap(category => category.agents);
};

export const getAgentById = (id: string): Agent | undefined => {
  return getAllAgents().find(agent => agent.id === id);
};

export const getAgentsByCategory = (categoryId: string): Agent[] => {
  const category = AGENT_CATEGORIES.find(cat => cat.id === categoryId);
  return category ? category.agents : [];
};

export const getAgentsByEngine = (engineType: Agent['engineType']): Agent[] => {
  return getAllAgents().filter(agent => agent.engineType === engineType);
};

export const getAgentEmoji = (agentId: string): string => {
  const agent = getAgentById(agentId);
  return agent ? agent.icon : '🤖';
};

export const getAgentColor = (agentId: string): string => {
  const agent = getAgentById(agentId);
  return agent ? agent.color : '#6B7280';
};