import { SessionHistory } from '../components/sessions/SessionHistory';

interface HistoryPageProps {
  onViewChange?: (view: 'wizard' | 'history') => void;
}

export function HistoryPage({ onViewChange }: HistoryPageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-primary-dark mb-2">
              Historique des analyses
            </h1>
            <p className="text-gray-600">
              Consultez, gérez et supprimez vos sessions d'analyse précédentes
            </p>
          </div>

          {/* Session History Component */}
          <SessionHistory onViewChange={onViewChange} />
        </div>
      </div>
    </div>
  );
}
