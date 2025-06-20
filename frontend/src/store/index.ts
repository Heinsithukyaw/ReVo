import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { AgentState, createAgentSlice } from './agentSlice';
import { ChatState, createChatSlice } from './chatSlice';
import { SystemState, createSystemSlice } from './systemSlice';

export interface AppState extends AgentState, ChatState, SystemState {}

export const useAppStore = create<AppState>()(
  devtools(
    subscribeWithSelector(
      (...a) => ({
        ...createAgentSlice(...a),
        ...createChatSlice(...a),
        ...createSystemSlice(...a),
      })
    ),
    {
      name: 'revoagent-store',
    }
  )
);

export default useAppStore;