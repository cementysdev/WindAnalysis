import { WizardProvider } from "./wizard/WizardContext";
import { AppContent } from "./AppContent";

function App() {
  return (
    <WizardProvider>
      <AppContent />
    </WizardProvider>
  );
}

export default App;
