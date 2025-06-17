import { useState, useCallback, useEffect } from 'react';
import { getAllAgents, Agent } from '../constants/agents';

export const useAgentSelection = () => {
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [agentHistory, setAgentHistory] = useState<string[]>([]);
  const [favoriteAgents, setFavoriteAgents] = useState<string[]>([]);

  // Load saved preferences from localStorage
  useEffect(() => {
    try {
      const savedSelection = localStorage.getItem('revoagent-selected-agents');
      const savedFavorites = localStorage.getItem('revoagent-favorite-agents');
      const savedHistory = localStorage.getItem('revoagent-agent-history');

      if (savedSelection) {
        setSelectedAgents(JSON.parse(savedSelection));
      }
      if (savedFavorites) {
        setFavoriteAgents(JSON.parse(savedFavorites));
      }
      if (savedHistory) {
        setAgentHistory(JSON.parse(savedHistory));
      }
    } catch (error) {
      console.error('Failed to load agent preferences:', error);
    }
  }, []);

  // Save preferences to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('revoagent-selected-agents', JSON.stringify(selectedAgents));
    } catch (error) {
      console.error('Failed to save selected agents:', error);
    }
  }, [selectedAgents]);

  useEffect(() => {
    try {
      localStorage.setItem('revoagent-favorite-agents', JSON.stringify(favoriteAgents));
    } catch (error) {
      console.error('Failed to save favorite agents:', error);
    }
  }, [favoriteAgents]);

  useEffect(() => {
    try {
      localStorage.setItem('revoagent-agent-history', JSON.stringify(agentHistory));
    } catch (error) {
      console.error('Failed to save agent history:', error);
    }
  }, [agentHistory]);

  // Toggle agent selection
  const toggleAgent = useCallback((agentId: string) => {
    setSelectedAgents(prev => {
      const isSelected = prev.includes(agentId);
      let newSelection;
      
      if (isSelected) {
        newSelection = prev.filter(id => id !== agentId);
      } else {
        newSelection = [...prev, agentId];
        
        // Add to history if not already there
        setAgentHistory(prevHistory => {
          const newHistory = [agentId, ...prevHistory.filter(id => id !== agentId)];
          return newHistory.slice(0, 20); // Keep only last 20 agents
        });
      }
      
      return newSelection;
    });
  }, []);

  // Select multiple agents
  const selectAgents = useCallback((agentIds: string[]) => {
    const validAgentIds = agentIds.filter(id => 
      getAllAgents().some(agent => agent.id === id)
    );
    setSelectedAgents(validAgentIds);
    
    // Add to history
    validAgentIds.forEach(agentId => {
      setAgentHistory(prevHistory => {
        const newHistory = [agentId, ...prevHistory.filter(id => id !== agentId)];
        return newHistory.slice(0, 20);
      });
    });
  }, []);

  // Clear all selected agents
  const clearSelection = useCallback(() => {
    setSelectedAgents([]);
  }, []);

  // Select agents by category
  const selectByCategory = useCallback((categoryId: string) => {
    const agents = getAllAgents().filter(agent => agent.category === categoryId);
    const agentIds = agents.map(agent => agent.id);
    selectAgents(agentIds);
  }, [selectAgents]);

  // Select agents by engine type
  const selectByEngine = useCallback((engineType: Agent['engineType']) => {
    const agents = getAllAgents().filter(agent => agent.engineType === engineType);
    const agentIds = agents.map(agent => agent.id);
    selectAgents(agentIds);
  }, [selectAgents]);

  // Toggle favorite agent
  const toggleFavorite = useCallback((agentId: string) => {
    setFavoriteAgents(prev => {
      const isFavorite = prev.includes(agentId);
      if (isFavorite) {
        return prev.filter(id => id !== agentId);
      } else {
        return [...prev, agentId];
      }
    });
  }, []);

  // Select favorite agents
  const selectFavorites = useCallback(() => {
    selectAgents(favoriteAgents);
  }, [favoriteAgents, selectAgents]);

  // Get recommended agents based on history and current selection
  const getRecommendedAgents = useCallback(() => {
    const allAgents = getAllAgents();
    const selectedCategories = selectedAgents.map(id => 
      allAgents.find(agent => agent.id === id)?.category
    ).filter(Boolean);
    
    const selectedEngineTypes = selectedAgents.map(id => 
      allAgents.find(agent => agent.id === id)?.engineType
    ).filter(Boolean);

    // Recommend agents from same categories or complementary engine types
    const recommendations = allAgents.filter(agent => {
      if (selectedAgents.includes(agent.id)) return false;
      
      // Recommend from same categories
      if (selectedCategories.includes(agent.category)) return true;
      
      // Recommend complementary engine types
      if (selectedEngineTypes.length > 0 && !selectedEngineTypes.includes(agent.engineType)) {
        return true;
      }
      
      // Recommend from history
      if (agentHistory.includes(agent.id)) return true;
      
      return false;
    });

    // Sort by history recency and favorites
    return recommendations.sort((a, b) => {
      const aIsFavorite = favoriteAgents.includes(a.id);
      const bIsFavorite = favoriteAgents.includes(b.id);
      
      if (aIsFavorite && !bIsFavorite) return -1;
      if (!aIsFavorite && bIsFavorite) return 1;
      
      const aHistoryIndex = agentHistory.indexOf(a.id);
      const bHistoryIndex = agentHistory.indexOf(b.id);
      
      if (aHistoryIndex === -1 && bHistoryIndex === -1) return 0;
      if (aHistoryIndex === -1) return 1;
      if (bHistoryIndex === -1) return -1;
      
      return aHistoryIndex - bHistoryIndex;
    }).slice(0, 10);
  }, [selectedAgents, agentHistory, favoriteAgents]);

  // Quick selection presets
  const selectPreset = useCallback((presetName: string) => {
    const presets: { [key: string]: string[] } = {
      'fullstack': ['fullstack-dev', 'backend-architect', 'frontend-specialist', 'devops-engineer'],
      'ai-team': ['ml-engineer', 'data-scientist', 'nlp-specialist', 'computer-vision'],
      'business': ['business-analyst', 'product-manager', 'marketing-strategist', 'financial-analyst'],
      'creative': ['ui-designer', 'ux-researcher', 'content-creator', 'graphic-designer'],
      'security': ['security-analyst', 'compliance-officer', 'penetration-tester'],
      'operations': ['system-admin', 'qa-engineer', 'support-specialist'],
      'three-engine': ['ml-engineer', 'fullstack-dev', 'ui-designer'], // One from each engine type
      'startup': ['fullstack-dev', 'product-manager', 'ui-designer', 'marketing-strategist'],
      'enterprise': ['backend-architect', 'security-analyst', 'business-analyst', 'devops-engineer']
    };

    if (presets[presetName]) {
      selectAgents(presets[presetName]);
    }
  }, [selectAgents]);

  // Get selection statistics
  const getSelectionStats = useCallback(() => {
    const allAgents = getAllAgents();
    const selectedAgentObjects = selectedAgents.map(id => 
      allAgents.find(agent => agent.id === id)
    ).filter(Boolean) as Agent[];

    const categoryCount: { [key: string]: number } = {};
    const engineCount: { [key: string]: number } = {};

    selectedAgentObjects.forEach(agent => {
      categoryCount[agent.category] = (categoryCount[agent.category] || 0) + 1;
      engineCount[agent.engineType] = (engineCount[agent.engineType] || 0) + 1;
    });

    return {
      total: selectedAgents.length,
      categories: categoryCount,
      engines: engineCount,
      hasThreeEngines: Object.keys(engineCount).length >= 3,
      isBalanced: Object.values(categoryCount).every(count => count <= 3)
    };
  }, [selectedAgents]);

  return {
    selectedAgents,
    agentHistory,
    favoriteAgents,
    toggleAgent,
    selectAgents,
    clearSelection,
    selectByCategory,
    selectByEngine,
    toggleFavorite,
    selectFavorites,
    getRecommendedAgents,
    selectPreset,
    getSelectionStats
  };
};