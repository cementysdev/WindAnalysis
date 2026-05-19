import { useState } from 'react';
import { WizardProvider } from "./wizard/WizardContext";
import { WizardContainer } from "./wizard/WizardContainer";
import { HistoryPage } from "./pages/HistoryPage";
import { MainLayout } from "./components/layout/MainLayout";

function App() {
  const [currentView, setCurrentView] = useState<'wizard' | 'history'>('wizard');

  return (
    <WizardProvider>
      <MainLayout currentView={currentView} onViewChange={setCurrentView}>
        {currentView === 'wizard' ? (
          <WizardContainer />
        ) : (
          <HistoryPage onViewChange={setCurrentView} />
        )}
      </MainLayout>
    </WizardProvider>
  );
}

export default App;
