import axios from "axios";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  UploadResponse,
  WorkflowType,
  SessionSummary,
  SessionDetail
} from "../types/analysis";

// Auto-detect API URL based on environment
const API_BASE_URL = (() => {
  // Development mode: use VITE_API_URL or default to localhost
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  // Production mode: frontend served by FastAPI, API on same origin
  return window.location.origin;
})();

console.log('[API Client] Base URL:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,  // 5 minutes (synchrone avec timeout étendu)
  headers: {
    "Content-Type": "application/json",
  },
});

export const analyzeAPI = {
  /**
   * Upload un fichier ZIP et crée une session
   */
  uploadZip: async (file: File, workflowType: WorkflowType): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("workflow_type", workflowType);

    const response = await axios.post<UploadResponse>(
      `${API_BASE_URL}/upload`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 60000, // 1 minute pour l'upload
      }
    );

    return response.data;
  },

  /**
   * Déclenche une analyse RunTest ou SCADA
   */
  runAnalysis: async (request: AnalyzeRequest): Promise<AnalyzeResponse> => {
    const endpoint = request.workflow_type === "runtest" ? "/analyze/runtest" : "/analyze/scada";
    const response = await apiClient.post<AnalyzeResponse>(endpoint, request);
    return response.data;
  },

  /**
   * Lit le fichier config.yml sans lancer l'analyse
   */
  readConfig: async (folderPathOrSessionId: string, isSessionId: boolean = false): Promise<any> => {
    const params = isSessionId
      ? { session_id: folderPathOrSessionId }
      : { folder_path: folderPathOrSessionId };

    const response = await apiClient.get("/config", { params });
    return response.data;
  },

  /**
   * Vérifie l'état de santé de l'API
   */
  healthCheck: async (): Promise<{ status: string; version: string }> => {
    const response = await apiClient.get("/health");
    return response.data;
  },

  /**
   * Liste toutes les sessions
   */
  listSessions: async (): Promise<SessionSummary[]> => {
    const response = await apiClient.get<SessionSummary[]>("/sessions");
    return response.data;
  },

  /**
   * Récupère les détails d'une session
   */
  getSessionDetails: async (sessionId: string): Promise<SessionDetail> => {
    const response = await apiClient.get<SessionDetail>(`/sessions/${sessionId}`);
    return response.data;
  },

  /**
   * Supprime une session
   */
  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/sessions/${sessionId}`);
  },

  /**
   * Supprime plusieurs sessions en batch
   */
  deleteMultipleSessions: async (sessionIds: string[]): Promise<{ results: Record<string, string>; deleted_count: number; failed_count: number }> => {
    const response = await apiClient.delete("/sessions", {
      data: { session_ids: sessionIds }
    });
    return response.data;
  },

  /**
   * Télécharge le rapport Word d'une session
   */
  downloadReport: async (sessionId: string): Promise<void> => {
    // Use window.open to trigger download
    const url = `${API_BASE_URL}/sessions/${sessionId}/report`;
    window.open(url, '_blank');
  },
};
