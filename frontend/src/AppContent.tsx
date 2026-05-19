import { useState } from 'react';
import { useWizard } from "./hooks/useWizard";
import { WizardContainer } from "./wizard/WizardContainer";
import { HistoryPage } from "./pages/HistoryPage";
import { MainLayout } from "./components/layout/MainLayout";

export function AppContent() {
  const [currentView, setCurrentView] = useState<'wizard' | 'history'>('wizard');
  const { reset, goToStep } = useWizard();

  const handleNewAnalysis = () => {
    reset();
    goToStep('dataSource');
  };

  return (
    <MainLayout
      currentView={currentView}
      onViewChange={setCurrentView}
      onNewAnalysis={handleNewAnalysis}
    >
      {currentView === 'wizard' ? (
        <WizardContainer />
      ) : (
        <HistoryPage onViewChange={setCurrentView} />
      )}
    </MainLayout>
  );
}
