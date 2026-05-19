import type { AnalyzeResponse } from './analysis';
import type { ParsedConfig } from './config';

export type WizardStep = 'dataSource' | 'configReview' | 'results';

export interface WizardState {
  currentStep: WizardStep;
  folderPath: string | null;  // Legacy mode
  sessionId: string | null;   // New session mode
  uploadedFile: File | null;  // File selected for upload
  workflowType: 'runtest' | 'scada' | null;
  configData: ParsedConfig | null;
  analysisResult: AnalyzeResponse | null;
  isLoading: boolean;
  error: string | null;
}

export type WizardAction =
  | { type: 'SET_STEP'; payload: WizardStep }
  | { type: 'SET_FOLDER_PATH'; payload: string }
  | { type: 'SET_SESSION_ID'; payload: string }
  | { type: 'SET_UPLOADED_FILE'; payload: File }
  | { type: 'SET_WORKFLOW_TYPE'; payload: 'runtest' | 'scada' }
  | { type: 'SET_CONFIG_DATA'; payload: ParsedConfig }
  | { type: 'SET_ANALYSIS_RESULT'; payload: AnalyzeResponse }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET' };
