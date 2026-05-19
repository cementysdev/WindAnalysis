import { createContext, useReducer, type ReactNode } from 'react';
import type { WizardState, WizardAction, WizardStep } from '../types/wizard';
import type { AnalyzeResponse } from '../types/analysis';
import type { ParsedConfig } from '../types/config';

const initialState: WizardState = {
  currentStep: 'dataSource',
  folderPath: null,
  sessionId: null,
  uploadedFile: null,
  workflowType: null,
  configData: null,
  analysisResult: null,
  isLoading: false,
  error: null,
};

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, currentStep: action.payload };

    case 'SET_FOLDER_PATH':
      return { ...state, folderPath: action.payload };

    case 'SET_SESSION_ID':
      return { ...state, sessionId: action.payload };

    case 'SET_UPLOADED_FILE':
      return { ...state, uploadedFile: action.payload };

    case 'SET_WORKFLOW_TYPE':
      return { ...state, workflowType: action.payload };

    case 'SET_CONFIG_DATA':
      return { ...state, configData: action.payload };

    case 'SET_ANALYSIS_RESULT':
      return { ...state, analysisResult: action.payload };

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

export interface WizardContextValue {
  state: WizardState;
  dispatch: React.Dispatch<WizardAction>;
  // Helper functions for common actions
  goToStep: (step: WizardStep) => void;
  nextStep: () => void;
  previousStep: () => void;
  setFolderPath: (path: string) => void;
  setSessionId: (sessionId: string) => void;
  setUploadedFile: (file: File) => void;
  setWorkflowType: (type: 'runtest' | 'scada') => void;
  setConfigData: (config: ParsedConfig) => void;
  setAnalysisResult: (result: AnalyzeResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const WizardContext = createContext<WizardContextValue | null>(null);

interface WizardProviderProps {
  children: ReactNode;
}

export function WizardProvider({ children }: WizardProviderProps) {
  const [state, dispatch] = useReducer(wizardReducer, initialState);

  const stepOrder: WizardStep[] = ['dataSource', 'configReview', 'results'];

  const goToStep = (step: WizardStep) => {
    dispatch({ type: 'SET_STEP', payload: step });
  };

  const nextStep = () => {
    const currentIndex = stepOrder.indexOf(state.currentStep);
    if (currentIndex < stepOrder.length - 1) {
      dispatch({ type: 'SET_STEP', payload: stepOrder[currentIndex + 1] });
    }
  };

  const previousStep = () => {
    const currentIndex = stepOrder.indexOf(state.currentStep);
    if (currentIndex > 0) {
      dispatch({ type: 'SET_STEP', payload: stepOrder[currentIndex - 1] });
    }
  };

  const setFolderPath = (path: string) => {
    dispatch({ type: 'SET_FOLDER_PATH', payload: path });
  };

  const setSessionId = (sessionId: string) => {
    dispatch({ type: 'SET_SESSION_ID', payload: sessionId });
  };

  const setUploadedFile = (file: File) => {
    dispatch({ type: 'SET_UPLOADED_FILE', payload: file });
  };

  const setWorkflowType = (type: 'runtest' | 'scada') => {
    dispatch({ type: 'SET_WORKFLOW_TYPE', payload: type });
  };

  const setConfigData = (config: ParsedConfig) => {
    dispatch({ type: 'SET_CONFIG_DATA', payload: config as any });
  };

  const setAnalysisResult = (result: AnalyzeResponse) => {
    dispatch({ type: 'SET_ANALYSIS_RESULT', payload: result });
  };

  const setLoading = (loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const setError = (error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };

  const reset = () => {
    dispatch({ type: 'RESET' });
  };

  const value: WizardContextValue = {
    state,
    dispatch,
    goToStep,
    nextStep,
    previousStep,
    setFolderPath,
    setSessionId,
    setUploadedFile,
    setWorkflowType,
    setConfigData,
    setAnalysisResult,
    setLoading,
    setError,
    reset,
  };

  return (
    <WizardContext.Provider value={value}>
      {children}
    </WizardContext.Provider>
  );
}
