import { useEffect, useCallback } from 'react';
import { useAppStore } from '../store';
import { Agent, AgentTask, AgentConfiguration } from '../types/agents';
import apiClient from '../services/api';

export const useAgents = () => {
  const {
    agents,
    selectedAgent,
    agentTasks,
    agentConfigurations,
    isLoading,
    error,
    setAgents,
    setSelectedAgent,
    addAgent,
    updateAgent,
    removeAgent,
    setAgentTasks,
    addAgentTask,
    updateAgentTask,
    setAgentConfigurations,
    setLoading,
    setError,
  } = useAppStore();

  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/agents');
      setAgents(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
    } finally {
      setLoading(false);
    }
  }, [setAgents, setLoading, setError]);

  const fetchAgentTasks = useCallback(async () => {
    try {
      const response = await apiClient.get('/agents/tasks');
      setAgentTasks(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent tasks');
    }
  }, [setAgentTasks, setError]);

  const fetchAgentConfigurations = useCallback(async () => {
    try {
      const response = await apiClient.get('/agents/configurations');
      setAgentConfigurations(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent configurations');
    }
  }, [setAgentConfigurations, setError]);

  const createAgent = useCallback(async (agentData: Omit<Agent, 'id'>) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/agents', agentData);
      addAgent(response.data);
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addAgent, setLoading, setError]);

  const updateAgentById = useCallback(async (id: string, updates: Partial<Agent>) => {
    try {
      setLoading(true);
      const response = await apiClient.put(`/agents/${id}`, updates);
      updateAgent(id, response.data);
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update agent');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [updateAgent, setLoading, setError]);

  const deleteAgent = useCallback(async (id: string) => {
    try {
      setLoading(true);
      await apiClient.delete(`/agents/${id}`);
      removeAgent(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete agent');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [removeAgent, setLoading, setError]);

  const executeAgentTask = useCallback(async (agentId: string, taskData: any) => {
    try {
      setLoading(true);
      const response = await apiClient.post(`/agents/${agentId}/execute`, taskData);
      addAgentTask(response.data);
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute agent task');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addAgentTask, setLoading, setError]);

  // Initialize data on mount
  useEffect(() => {
    fetchAgents();
    fetchAgentTasks();
    fetchAgentConfigurations();
  }, [fetchAgents, fetchAgentTasks, fetchAgentConfigurations]);

  return {
    // State
    agents,
    selectedAgent,
    agentTasks,
    agentConfigurations,
    isLoading,
    error,
    
    // Actions
    setSelectedAgent,
    fetchAgents,
    fetchAgentTasks,
    fetchAgentConfigurations,
    createAgent,
    updateAgent: updateAgentById,
    deleteAgent,
    executeAgentTask,
  };
};