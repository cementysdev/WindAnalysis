import { useState, useEffect } from 'react';
import { Eye, Trash2, Loader2, AlertCircle, RefreshCw, Calendar, Activity, Download } from 'lucide-react';
import { analyzeAPI } from '../../services/api';
import { useWizard } from '../../hooks/useWizard';
import type { SessionSummary } from '../../types/analysis';

interface SessionHistoryProps {
  onViewChange?: (view: 'wizard' | 'history') => void;
}

export function SessionHistory({ onViewChange }: SessionHistoryProps) {
  const { reset, setSessionId, setWorkflowType, setConfigData, setAnalysisResult, goToStep } = useWizard();

  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await analyzeAPI.listSessions();
      setSessions(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erreur lors du chargement des sessions';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewSession = async (sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Load session details from backend
      const details = await analyzeAPI.getSessionDetails(sessionId);

      // Find the session summary for workflow_type
      const sessionSummary = sessions.find(s => s.session_id === sessionId);
      if (!sessionSummary) {
        throw new Error('Session not found');
      }

      // Reset wizard state
      reset();

      // Set session data
      setSessionId(sessionId);
      setWorkflowType(sessionSummary.workflow_type);
      setConfigData(details.metadata);

      // Set analysis result
      setAnalysisResult({
        status: 'success',
        message: `Session ${sessionId} chargée`,
        charts: details.charts,
        tables: details.tables,
        metadata: details.metadata,
      });

      // Navigate to results step
      goToStep('results');

      // Switch to wizard view
      if (onViewChange) {
        onViewChange('wizard');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erreur lors du chargement de la session';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSessions = async () => {
    if (selectedSessions.size === 0) return;

    const confirmed = window.confirm(
      `Voulez-vous vraiment supprimer ${selectedSessions.size} session(s) ?\n\nCette action est irréversible.`
    );

    if (!confirmed) return;

    setIsDeleting(true);
    setError(null);

    try {
      const sessionIds = Array.from(selectedSessions);
      const result = await analyzeAPI.deleteMultipleSessions(sessionIds);

      console.log('Bulk delete result:', result);

      // Clear selection
      setSelectedSessions(new Set());

      // Reload sessions
      await loadSessions();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erreur lors de la suppression des sessions';
      setError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  const toggleSessionSelection = (sessionId: string) => {
    const newSet = new Set(selectedSessions);
    if (newSet.has(sessionId)) {
      newSet.delete(sessionId);
    } else {
      newSet.add(sessionId);
    }
    setSelectedSessions(newSet);
  };

  const toggleSelectAll = () => {
    if (selectedSessions.size === sessions.length) {
      setSelectedSessions(new Set());
    } else {
      setSelectedSessions(new Set(sessions.map(s => s.session_id)));
    }
  };

  const formatDate = (isoDate: string): string => {
    try {
      const date = new Date(isoDate);
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoDate;
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100';
      case 'created':
        return 'text-blue-700 bg-blue-100';
      case 'error':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'Complétée';
      case 'created':
        return 'Créée';
      case 'error':
        return 'Erreur';
      default:
        return status;
    }
  };

  if (isLoading && sessions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-12 h-12 text-primary-dark animate-spin mb-4" />
          <p className="text-gray-600">Chargement de l'historique...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-xl font-bold text-gray-900">Historique des analyses</h3>
            <p className="text-sm text-gray-600 mt-1">
              {sessions.length} session{sessions.length > 1 ? 's' : ''} trouvée{sessions.length > 1 ? 's' : ''}
            </p>
          </div>

          <div className="flex space-x-3">
            {selectedSessions.size > 0 && (
              <button
                onClick={handleDeleteSessions}
                disabled={isDeleting}
                className="bg-red-600 text-white px-4 py-2 rounded-md font-semibold hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Suppression...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Supprimer ({selectedSessions.size})
                  </>
                )}
              </button>
            )}

            <button
              onClick={loadSessions}
              disabled={isLoading}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md font-semibold hover:bg-gray-200 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Actualiser
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="m-6 bg-red-50 border border-red-200 rounded-md p-4 flex items-start">
          <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-red-900 mb-1">Erreur</h4>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Sessions Table */}
      {sessions.length === 0 ? (
        <div className="p-12 text-center">
          <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">Aucune analyse dans l'historique</p>
          <p className="text-sm text-gray-400 mt-2">
            Les sessions apparaîtront ici après avoir uploadé et analysé des fichiers
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedSessions.size === sessions.length && sessions.length > 0}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 text-primary-dark rounded focus:ring-primary-dark"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Parc éolien
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Résultats
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sessions.map((session) => (
                <tr
                  key={session.session_id}
                  className={`hover:bg-gray-50 transition-colors ${
                    selectedSessions.has(session.session_id) ? 'bg-blue-50' : ''
                  }`}
                >
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedSessions.has(session.session_id)}
                      onChange={() => toggleSessionSelection(session.session_id)}
                      className="w-4 h-4 text-primary-dark rounded focus:ring-primary-dark"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {session.park_name || 'Sans nom'}
                    </div>
                    <div className="text-xs text-gray-500 font-mono">
                      {session.session_id.slice(0, 8)}...
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-700">
                      {session.workflow_type === 'runtest' ? 'RunTest' : 'SCADA'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center text-sm text-gray-700">
                      <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                      {formatDate(session.created_at)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(session.status)}`}>
                      {getStatusLabel(session.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {session.charts_count} graphiques, {session.tables_count} tableaux
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      {session.status === 'completed' && (
                        <button
                          onClick={() => analyzeAPI.downloadReport(session.session_id)}
                          disabled={isLoading}
                          className="inline-flex items-center bg-blue-600 text-white px-3 py-1.5 rounded-md text-sm font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                          title="Télécharger le rapport"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleViewSession(session.session_id)}
                        disabled={isLoading}
                        className="inline-flex items-center bg-primary-dark text-white px-3 py-1.5 rounded-md text-sm font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                      >
                        <Eye className="w-4 h-4 mr-1.5" />
                        Consulter
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
