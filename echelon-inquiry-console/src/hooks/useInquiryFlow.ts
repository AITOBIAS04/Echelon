import {
  createContext,
  useContext,
  useReducer,
  type ReactNode,
  type Dispatch,
} from 'react';
import React from 'react';
import type { Signal, InquiryClass } from '../types/signal';
import type { TheatreTemplate, CommitmentTarget } from '../types/inquiry';
import type { Episode, MarketPhase } from '../types/execution';
import type { CalibrationCertificate } from '../types/certificate';
import { COMMITMENT_TARGETS } from '../data/templates';

export interface InquiryFlowState {
  currentStep: 1 | 2 | 3 | 4 | 5;
  selectedSignal: Signal | null;
  selectedClass: InquiryClass | null;
  selectedTemplate: TheatreTemplate | null;
  commitmentTarget: CommitmentTarget | null;
  isCommitted: boolean;
  executionProgress: {
    currentEpisode: number;
    totalEpisodes: number;
    completedEpisodes: Episode[];
    currentPhase: number;
    totalPhases: number;
    completedPhases: MarketPhase[];
    isComplete: boolean;
  };
  certificate: CalibrationCertificate | null;
}

export type InquiryAction =
  | { type: 'SELECT_SIGNAL'; payload: Signal }
  | { type: 'SELECT_CLASS'; payload: InquiryClass }
  | { type: 'SELECT_TEMPLATE'; payload: TheatreTemplate }
  | { type: 'COMMIT' }
  | { type: 'ADVANCE_EPISODE'; payload: Episode }
  | { type: 'ADVANCE_PHASE'; payload: MarketPhase }
  | { type: 'COMPLETE_EXECUTION' }
  | { type: 'SET_CERTIFICATE'; payload: CalibrationCertificate }
  | { type: 'GO_TO_STEP'; payload: 1 | 2 | 3 | 4 | 5 }
  | { type: 'RESET' };

const initialState: InquiryFlowState = {
  currentStep: 1,
  selectedSignal: null,
  selectedClass: null,
  selectedTemplate: null,
  commitmentTarget: null,
  isCommitted: false,
  executionProgress: {
    currentEpisode: 0,
    totalEpisodes: 0,
    completedEpisodes: [],
    currentPhase: 0,
    totalPhases: 0,
    completedPhases: [],
    isComplete: false,
  },
  certificate: null,
};

function inquiryReducer(
  state: InquiryFlowState,
  action: InquiryAction
): InquiryFlowState {
  switch (action.type) {
    case 'SELECT_SIGNAL':
      return {
        ...state,
        currentStep: 2,
        selectedSignal: action.payload,
        selectedClass: action.payload.suggested_class,
        selectedTemplate: null,
        commitmentTarget: null,
        isCommitted: false,
        executionProgress: initialState.executionProgress,
        certificate: null,
      };

    case 'SELECT_CLASS':
      return {
        ...state,
        selectedClass: action.payload,
        selectedTemplate: null,
        commitmentTarget: null,
        isCommitted: false,
      };

    case 'SELECT_TEMPLATE':
      return {
        ...state,
        selectedTemplate: action.payload,
        commitmentTarget:
          COMMITMENT_TARGETS[action.payload.template_id] ?? null,
        isCommitted: false,
      };

    case 'COMMIT':
      return {
        ...state,
        isCommitted: true,
      };

    case 'ADVANCE_EPISODE':
      return {
        ...state,
        executionProgress: {
          ...state.executionProgress,
          currentEpisode: state.executionProgress.currentEpisode + 1,
          completedEpisodes: [
            ...state.executionProgress.completedEpisodes,
            action.payload,
          ],
        },
      };

    case 'ADVANCE_PHASE':
      return {
        ...state,
        executionProgress: {
          ...state.executionProgress,
          currentPhase: state.executionProgress.currentPhase + 1,
          completedPhases: [
            ...state.executionProgress.completedPhases,
            { ...action.payload, status: 'complete' as const },
          ],
        },
      };

    case 'COMPLETE_EXECUTION':
      return {
        ...state,
        currentStep: 4,
        executionProgress: {
          ...state.executionProgress,
          isComplete: true,
        },
      };

    case 'SET_CERTIFICATE':
      return {
        ...state,
        currentStep: 4,
        certificate: action.payload,
      };

    case 'GO_TO_STEP': {
      const target = action.payload;
      // Allow backward navigation to completed steps or forward to next step
      if (target <= state.currentStep) {
        return { ...state, currentStep: target };
      }
      return state;
    }

    case 'RESET':
      return { ...initialState };

    default:
      return state;
  }
}

const InquiryFlowContext = createContext<
  [InquiryFlowState, Dispatch<InquiryAction>] | null
>(null);

export function InquiryFlowProvider({ children }: { children: ReactNode }) {
  const value = useReducer(inquiryReducer, initialState);

  return React.createElement(
    InquiryFlowContext.Provider,
    { value },
    children
  );
}

export function useInquiryFlow(): [InquiryFlowState, Dispatch<InquiryAction>] {
  const ctx = useContext(InquiryFlowContext);
  if (!ctx) {
    throw new Error('useInquiryFlow must be used within InquiryFlowProvider');
  }
  return ctx;
}
