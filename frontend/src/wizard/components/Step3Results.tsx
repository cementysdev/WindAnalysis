import { useEffect, useRef } from 'react';
import { useWizard } from '../../hooks/useWizard';
import { analyzeAPI } from '../../services/api';
import { RunTestResults } from '../../components/results/RunTestResults';
import { ScadaResults } from '../../components/results/ScadaResults';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';

export function Step3Results() {
  const { state, setAnalysisResult, setLoading, setError, previousStep, reset } = useWizard();
  const hasTriggeredRef = useRef(false);

  // Trigger analysis when component mounts if no result yet
  useEffect(() => {
    if (!hasTriggeredRef.current && !state.analysisResult && state.folderPath && state.workflowType && !state.isLoading) {
      hasTriggeredRef.current = true;
      triggerAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps array = run only once on mount

  const triggerAnalysis = async () => {
    if (!state.folderPath || !state.workflowType) {
      setError('Configuration manquante. Veuillez retourner à l\'étape 1.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🚀 Lancement de l\'analyse...', {
        folder: state.folderPath,
        workflow: state.workflowType,
      });

      const response = await analyzeAPI.runAnalysis({
        folder_path: state.folderPath,
        workflow_type: state.workflowType,
        render_template: true,
      });

      console.log('✅ Analyse terminée:', response);
      setAnalysisResult(response);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erreur lors de l\'analyse';
      console.error('❌ Erreur analyse:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (state.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-16 h-16 text-primary-dark animate-spin mb-6" />
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Analyse en cours...</h3>
        <p className="text-gray-600 mb-4">Cette opération peut prendre entre 1 et 5 minutes.</p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-2xl mx-auto">
          <p className="text-sm text-blue-900 break-all">
            <strong>Dossier :</strong> {state.folderPath}
          </p>
          <p className="text-sm text-blue-900 mt-2">
            <strong>Type :</strong> {state.workflowType === 'runtest' ? 'RunTest' : 'SCADA'}
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (state.error) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-primary-dark mb-6">
          Étape 3 : Résultats de l'analyse
        </h2>

        <div className="bg-red-50 border border-red-200 rounded-md p-6 mb-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-red-900 font-semibold mb-2">Erreur lors de l'analyse</h3>
              <p className="text-sm text-red-800">{state.error}</p>
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={previousStep}
            className="bg-gray-500 text-white px-6 py-3 rounded-md font-semibold hover:bg-gray-600 transition-colors"
          >
            ← Retour à la configuration
          </button>
          <button
            onClick={triggerAnalysis}
            className="bg-primary-dark text-white px-6 py-3 rounded-md font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-5 h-5" />
            <span>Réessayer</span>
          </button>
        </div>
      </div>
    );
  }

  // No result yet (shouldn't happen because of useEffect)
  if (!state.analysisResult) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-12 h-12 text-gray-400 mb-4" />
        <p className="text-gray-600 mb-4">Aucun résultat disponible.</p>
        <button
          onClick={triggerAnalysis}
          className="bg-primary-dark text-white px-6 py-3 rounded-md font-semibold hover:bg-blue-700 transition-colors"
        >
          Lancer l'analyse
        </button>
      </div>
    );
  }

  // Display results
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-primary-dark">
          Résultats de l'analyse {state.workflowType === 'runtest' ? 'RunTest' : 'SCADA'}
        </h2>
        <button
          onClick={reset}
          className="bg-green-600 text-white px-6 py-2 rounded-md font-semibold hover:bg-green-700 transition-colors"
        >
          Nouvelle analyse
        </button>
      </div>

      {/* Metadata Summary */}
      {state.analysisResult.metadata && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            {state.analysisResult.metadata.park_name && (
              <div>
                <span className="font-semibold text-blue-900">Parc :</span>{' '}
                <span className="text-blue-800">{state.analysisResult.metadata.park_name}</span>
              </div>
            )}
            {state.analysisResult.metadata.turbines && (
              <div>
                <span className="font-semibold text-blue-900">Turbines :</span>{' '}
                <span className="text-blue-800">
                  {state.analysisResult.metadata.turbines.join(', ')}
                </span>
              </div>
            )}
            {state.analysisResult.metadata.test_start && state.analysisResult.metadata.test_end && (
              <div>
                <span className="font-semibold text-blue-900">Période :</span>{' '}
                <span className="text-blue-800">
                  {state.analysisResult.metadata.test_start} → {state.analysisResult.metadata.test_end}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results Layout */}
      {state.workflowType === 'runtest' ? (
        <RunTestResults result={state.analysisResult} />
      ) : (
        <ScadaResults result={state.analysisResult} />
      )}
    </div>
  );
}
