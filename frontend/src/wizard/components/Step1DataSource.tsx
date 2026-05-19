import { useState, useRef } from 'react';
import { Upload, Loader2, FileCheck, AlertCircle } from 'lucide-react';
import { useWizard } from '../../hooks/useWizard';
import { analyzeAPI } from '../../services/api';
import type { WorkflowType } from '../../types/analysis';

export function Step1DataSource() {
  const { state, setSessionId, setUploadedFile, setWorkflowType, setConfigData, nextStep, setError, setLoading } = useWizard();

  const [localWorkflowType, setLocalWorkflowType] = useState<WorkflowType>(
    state.workflowType || 'scada'
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(state.uploadedFile);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (file: File) => {
    // Validation
    if (!file.name.endsWith('.zip')) {
      setError('Seuls les fichiers .zip sont acceptés');
      return;
    }

    const maxSize = 100 * 1024 * 1024; // 100 MB
    if (file.size > maxSize) {
      setError('Le fichier doit faire moins de 100 MB');
      return;
    }

    setSelectedFile(file);
    setUploadedFile(file);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Veuillez sélectionner un fichier ZIP');
      return;
    }

    setIsUploading(true);
    setLoading(true);
    setError(null);

    try {
      // Upload ZIP to backend
      const response = await analyzeAPI.uploadZip(selectedFile, localWorkflowType);

      // Store session_id and config preview
      setSessionId(response.session_id);
      setWorkflowType(localWorkflowType);
      setConfigData(response.config_preview);

      // Auto-advance to next step
      nextStep();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erreur lors de l\'upload';
      setError(errorMessage);
    } finally {
      setIsUploading(false);
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-primary-dark mb-6">
        Étape 1 : Upload de fichier ZIP
      </h2>

      <div className="space-y-6">
        {/* Workflow Type Selection */}
        <div>
          <label htmlFor="workflowType" className="block text-gray-700 font-semibold mb-2">
            Type d'analyse
          </label>
          <select
            id="workflowType"
            value={localWorkflowType}
            onChange={(e) => setLocalWorkflowType(e.target.value as WorkflowType)}
            disabled={isUploading}
            className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-dark text-lg disabled:bg-gray-100"
          >
            <option value="runtest">RunTest - Réception d'éolienne</option>
            <option value="scada">SCADA - Surveillance continue</option>
          </select>
          <p className="mt-2 text-sm text-gray-600">
            {localWorkflowType === 'runtest'
              ? 'Analyse pour réception : 120h consécutives, puissance nominale, disponibilité.'
              : 'Analyse SCADA : EBA, codes d\'erreur, calibration, disponibilité des données.'}
          </p>
        </div>

        {/* File Upload Area */}
        <div>
          <label className="block text-gray-700 font-semibold mb-2">
            Fichier ZIP contenant config.yml et données
          </label>

          <div
            className={`border-2 border-dashed rounded-lg p-8 transition-colors ${
              dragActive
                ? 'border-primary-dark bg-blue-50'
                : selectedFile
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 bg-white'
            } ${isUploading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip"
              onChange={handleFileInputChange}
              disabled={isUploading}
              className="hidden"
            />

            {isUploading ? (
              <div className="flex flex-col items-center">
                <Loader2 className="w-12 h-12 text-primary-dark animate-spin mb-4" />
                <p className="text-lg font-semibold text-primary-dark">Upload en cours...</p>
                <p className="text-sm text-gray-500 mt-2">Extraction et validation du fichier</p>
              </div>
            ) : selectedFile ? (
              <div className="flex flex-col items-center">
                <FileCheck className="w-12 h-12 text-green-600 mb-4" />
                <p className="text-lg font-semibold text-gray-800">{selectedFile.name}</p>
                <p className="text-sm text-gray-500 mt-1">
                  Taille: {formatFileSize(selectedFile.size)}
                </p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                    setUploadedFile(null as any);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                  className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Choisir un autre fichier
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-lg font-semibold text-gray-700">
                  Glissez votre fichier ZIP ici
                </p>
                <p className="text-sm text-gray-500 mt-1">ou cliquez pour parcourir</p>
                <p className="text-xs text-gray-400 mt-3">
                  Maximum 100 MB • Format .zip uniquement
                </p>
              </div>
            )}
          </div>

          <p className="mt-2 text-sm text-gray-600">
            Le fichier ZIP doit contenir un <code className="bg-gray-100 px-1 py-0.5 rounded">config.yml</code> valide
            et les dossiers de données (operation_data, log_data).
          </p>
        </div>

        {/* Error Display */}
        {state.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-900 mb-1">Erreur</h3>
              <p className="text-sm text-red-800">{state.error}</p>
            </div>
          </div>
        )}

        {/* Information Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h3 className="font-semibold text-blue-900 mb-2">ℹ️ Information</h3>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Le fichier ZIP sera extrait et validé sur le serveur</li>
            <li>Une session temporaire sera créée pour stocker vos résultats</li>
            <li>À l'étape suivante, vous pourrez revoir la configuration avant de lancer l'analyse</li>
            <li>L'analyse complète peut prendre entre 1 et 5 minutes</li>
          </ul>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-4">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="bg-primary-dark text-white px-8 py-3 rounded-md font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Upload en cours...
              </>
            ) : (
              <>
                Upload et continuer →
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
