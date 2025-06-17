import { useState, useEffect, useCallback } from 'react';

interface EngineStatus {
  memory: {
    active: boolean;
    entities: number;
    speed: number;
    accuracy: number;
    relationships: number;
    dailyGrowth: number;
  };
  parallel: {
    active: boolean;
    tasks: number;
    throughput: number;
    efficiency: number;
    queueLength: number;
    avgResponseTime: number;
  };
  creative: {
    active: boolean;
    ideas: number;
    innovation: number;
    creativity: number;
    uniqueness: number;
    inspiration: number;
  };
  mcpTools?: {
    count: number;
    active: boolean;
  };
  revoComputer?: {
    status: string;
    active: boolean;
  };
}

interface CoordinationRequest {
  message: string;
  agents: string[];
  mode: 'collaborative' | 'sequential' | 'parallel';
}

interface CoordinationResponse {
  success: boolean;
  engineData: {
    memory?: any;
    parallel?: any;
    creative?: any;
  };
  response?: string;
  error?: string;
}

export const useThreeEngines = () => {
  const [engineStatus, setEngineStatus] = useState<EngineStatus>({
    memory: {
      active: true,
      entities: 1247893,
      speed: 95,
      accuracy: 99.9,
      relationships: 3456782,
      dailyGrowth: 2341
    },
    parallel: {
      active: true,
      tasks: 47,
      throughput: 87,
      efficiency: 94.2,
      queueLength: 12,
      avgResponseTime: 0.002
    },
    creative: {
      active: true,
      ideas: 156,
      innovation: 92,
      creativity: 88.5,
      uniqueness: 91.3,
      inspiration: 89.7
    },
    mcpTools: {
      count: 247,
      active: true
    },
    revoComputer: {
      status: 'Ready',
      active: true
    }
  });

  const [isCoordinating, setIsCoordinating] = useState(false);
  const [lastCoordination, setLastCoordination] = useState<CoordinationResponse | null>(null);

  // Fetch engine status from backend
  const fetchEngineStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/engines/status');
      if (response.ok) {
        const data = await response.json();
        setEngineStatus(prevStatus => ({
          ...prevStatus,
          ...data,
          // Ensure we maintain the structure even if backend doesn't return all fields
          memory: { ...prevStatus.memory, ...data.memory },
          parallel: { ...prevStatus.parallel, ...data.parallel },
          creative: { ...prevStatus.creative, ...data.creative }
        }));
      }
    } catch (error) {
      console.error('Failed to fetch engine status:', error);
      // Keep using mock data if backend is not available
    }
  }, []);

  // Coordinate engines for multi-agent response
  const coordinateEngines = useCallback(async (request: CoordinationRequest): Promise<CoordinationResponse> => {
    setIsCoordinating(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/engines/coordinate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: request.message,
          agents: request.agents,
          mode: request.mode,
          three_engine_mode: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        const coordinationResponse: CoordinationResponse = {
          success: true,
          engineData: data.engine_data || {},
          response: data.response
        };
        setLastCoordination(coordinationResponse);
        return coordinationResponse;
      } else {
        throw new Error(`Coordination failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Engine coordination error:', error);
      
      // Fallback coordination simulation
      const simulatedResponse: CoordinationResponse = {
        success: false,
        engineData: {
          memory: {
            entities: engineStatus.memory.entities,
            relevance: Math.floor(Math.random() * 100),
            contextLoaded: true
          },
          parallel: {
            tasks: engineStatus.parallel.tasks + 1,
            speed: Math.floor(Math.random() * 1000) + 100,
            efficiency: Math.floor(Math.random() * 100)
          },
          creative: {
            ideas: engineStatus.creative.ideas + Math.floor(Math.random() * 5),
            innovation: Math.floor(Math.random() * 100),
            uniqueness: Math.floor(Math.random() * 100)
          }
        },
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      
      setLastCoordination(simulatedResponse);
      return simulatedResponse;
    } finally {
      setIsCoordinating(false);
    }
  }, [engineStatus]);

  // Start engine coordination
  const startEngines = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/engines/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        await fetchEngineStatus();
      }
    } catch (error) {
      console.error('Failed to start engines:', error);
    }
  }, [fetchEngineStatus]);

  // Stop engine coordination
  const stopEngines = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/engines/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        setEngineStatus(prev => ({
          ...prev,
          memory: { ...prev.memory, active: false },
          parallel: { ...prev.parallel, active: false },
          creative: { ...prev.creative, active: false }
        }));
      }
    } catch (error) {
      console.error('Failed to stop engines:', error);
    }
  }, []);

  // Reset engine statistics
  const resetEngines = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/engines/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        await fetchEngineStatus();
      }
    } catch (error) {
      console.error('Failed to reset engines:', error);
    }
  }, [fetchEngineStatus]);

  // Periodic status updates
  useEffect(() => {
    fetchEngineStatus();
    
    const interval = setInterval(() => {
      fetchEngineStatus();
      
      // Simulate real-time updates for demo purposes
      setEngineStatus(prev => ({
        ...prev,
        memory: {
          ...prev.memory,
          entities: prev.memory.entities + Math.floor(Math.random() * 10),
          dailyGrowth: prev.memory.dailyGrowth + Math.floor(Math.random() * 5)
        },
        parallel: {
          ...prev.parallel,
          tasks: Math.max(0, prev.parallel.tasks + Math.floor(Math.random() * 6) - 3),
          queueLength: Math.max(0, prev.parallel.queueLength + Math.floor(Math.random() * 4) - 2)
        },
        creative: {
          ...prev.creative,
          ideas: prev.creative.ideas + Math.floor(Math.random() * 3)
        }
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchEngineStatus]);

  const threeEngineMode = engineStatus.memory.active && 
                          engineStatus.parallel.active && 
                          engineStatus.creative.active;

  return {
    engineStatus,
    memoryEngine: engineStatus.memory,
    parallelEngine: engineStatus.parallel,
    creativeEngine: engineStatus.creative,
    isCoordinating,
    lastCoordination,
    threeEngineMode,
    coordinationMode: 'balanced' as const,
    coordinateEngines,
    startCoordination: startEngines,
    stopCoordination: stopEngines,
    resetEngines,
    fetchEngineStatus
  };
};