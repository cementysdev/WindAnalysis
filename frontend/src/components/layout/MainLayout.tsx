import { History, Home } from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
  currentView: 'wizard' | 'history';
  onViewChange: (view: 'wizard' | 'history') => void;
  onNewAnalysis?: () => void;
}

export function MainLayout({ children, currentView, onViewChange, onNewAnalysis }: MainLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-primary-dark text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Wind Turbine Analytics</h1>
              <p className="text-sm text-blue-200 mt-1">
                Plateforme d'analyse de performance éolienne
              </p>
            </div>

            {/* Navigation */}
            <nav className="flex space-x-2">
              <button
                onClick={() => {
                  if (onNewAnalysis) {
                    onNewAnalysis();
                  }
                  onViewChange('wizard');
                }}
                className={`flex items-center px-4 py-2 rounded-md font-semibold transition-colors ${
                  currentView === 'wizard'
                    ? 'bg-white text-primary-dark'
                    : 'bg-blue-700 text-white hover:bg-blue-600'
                }`}
              >
                <Home className="w-4 h-4 mr-2" />
                Nouvelle analyse
              </button>

              <button
                onClick={() => onViewChange('history')}
                className={`flex items-center px-4 py-2 rounded-md font-semibold transition-colors ${
                  currentView === 'history'
                    ? 'bg-white text-primary-dark'
                    : 'bg-blue-700 text-white hover:bg-blue-600'
                }`}
              >
                <History className="w-4 h-4 mr-2" />
                Historique
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 py-4">
        <div className="container mx-auto px-4">
          <p className="text-center text-sm text-gray-600">
            Wind Turbine Analytics © 2026 - Analyse de performance et disponibilité
          </p>
        </div>
      </footer>
    </div>
  );
}
