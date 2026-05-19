import { useEffect } from 'react';
import { useWizard } from '../../hooks/useWizard';
import { useConfigParser } from '../../hooks/useConfigParser';
import { Tabs, type Tab } from '../../components/shared/Tabs';
import { GeneralInfoTab } from '../../components/config-review/GeneralInfoTab';
import { CriteriaTab } from '../../components/config-review/CriteriaTab';
import { TurbinesAccordion } from '../../components/config-review/TurbinesAccordion';
import { AdvancedTab } from '../../components/config-review/AdvancedTab';
import { Info, Target, Wind, Settings, Loader2, AlertCircle } from 'lucide-react';

export function Step2ConfigReview() {
  const { state, previousStep, nextStep, setConfigData, setError } = useWizard();
  const { loadConfig, isLoading, error: configError } = useConfigParser();

  useEffect(() => {
    // Load config when component mounts
    // Support both session_id (new) and folder_path (legacy)
    if (!state.configData) {
      if (state.sessionId) {
        // New mode: load from session_id
        loadConfig(state.sessionId, true).then((config) => {
          if (config) {
            setConfigData(config);
          } else if (configError) {
            setError(configError);
          }
        });
      } else if (state.folderPath) {
        // Legacy mode: load from folder_path
        loadConfig(state.folderPath, false).then((config) => {
          if (config) {
            setConfigData(config);
          } else if (configError) {
            setError(configError);
          }
        });
      }
    }
  }, [state.sessionId, state.folderPath, state.configData, loadConfig, setConfigData, setError, configError]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-12 h-12 text-primary-dark animate-spin mb-4" />
        <p className="text-gray-600">Chargement de la configuration...</p>
        <p className="text-sm text-gray-500 mt-2">
          {state.sessionId ? `Session: ${state.sessionId}` : state.folderPath}
        </p>
      </div>
    );
  }

  // Error state
  if (configError || !state.configData) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-primary-dark mb-6">
          Étape 2 : Revue de la configuration
        </h2>

        <div className="bg-red-50 border border-red-200 rounded-md p-6 mb-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-red-900 font-semibold mb-2">Erreur de chargement</h3>
              <p className="text-sm text-red-800">
                {configError || 'Impossible de charger le fichier config.yml'}
              </p>
              <p className="text-xs text-red-700 mt-2">
                Chemin : <code className="bg-red-100 px-2 py-1 rounded">{state.folderPath}</code>
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={previousStep}
            className="bg-gray-500 text-white px-6 py-2 rounded-md font-semibold hover:bg-gray-600 transition-colors"
          >
            ← Retour
          </button>
        </div>
      </div>
    );
  }

  const tabs: Tab[] = [
    {
      id: 'general',
      label: 'Informations générales',
      icon: <Info className="w-4 h-4" />,
      content: <GeneralInfoTab generalInfo={state.configData.general_information} />,
    },
    {
      id: 'criteria',
      label: 'Critères de validation',
      icon: <Target className="w-4 h-4" />,
      content: (
        <CriteriaTab
          criteria={state.configData.validation_criteria}
          workflowType={state.workflowType || 'runtest'}
        />
      ),
    },
    {
      id: 'turbines',
      label: 'Turbines',
      icon: <Wind className="w-4 h-4" />,
      content: <TurbinesAccordion turbines={state.configData.dynamic_fields?.turbines || []} />,
    },
    {
      id: 'advanced',
      label: 'Paramètres avancés',
      icon: <Settings className="w-4 h-4" />,
      content: <AdvancedTab config={state.configData} />,
    },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-primary-dark mb-6">
        Étape 2 : Revue de la configuration
      </h2>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
        <p className="text-sm text-blue-900">
          <strong>Dossier :</strong> {state.folderPath}
        </p>
        <p className="text-sm text-blue-900">
          <strong>Type d'analyse :</strong>{' '}
          {state.workflowType === 'runtest' ? 'RunTest (Réception)' : 'SCADA (Surveillance)'}
        </p>
      </div>

      {/* Tabs Component */}
      <Tabs tabs={tabs} defaultTab="general" />

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-6 border-t border-gray-200 mt-6">
        <button
          onClick={previousStep}
          className="bg-gray-500 text-white px-6 py-3 rounded-md font-semibold hover:bg-gray-600 transition-colors flex items-center space-x-2"
        >
          <span>← Retour</span>
        </button>
        <button
          onClick={nextStep}
          className="bg-primary-dark text-white px-6 py-3 rounded-md font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <span>Lancer l'analyse</span>
          <span>→</span>
        </button>
      </div>
    </div>
  );
}
