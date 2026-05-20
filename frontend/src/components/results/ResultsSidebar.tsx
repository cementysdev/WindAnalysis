import { ChevronRight, BarChart3, Table2 } from 'lucide-react';

export interface SidebarSection {
  id: string;
  label: string;
  icon?: React.ReactNode;
  chartsCount?: number;
  tablesCount?: number;
}

interface ResultsSidebarProps {
  sections: SidebarSection[];
  activeSection: string;
  onSectionChange: (sectionId: string) => void;
}

export function ResultsSidebar({ sections, activeSection, onSectionChange }: ResultsSidebarProps) {

  return (
    <aside className="w-64 bg-white rounded-lg shadow-lg p-4 sticky top-24 self-start">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-900 mb-1">Navigation</h3>
        <p className="text-xs text-gray-500">
          {sections.length} section{sections.length > 1 ? 's' : ''} disponible{sections.length > 1 ? 's' : ''}
        </p>
      </div>

      <nav className="space-y-1">
        {sections.map((section) => {
          const isActive = activeSection === section.id;
          const totalItems = (section.chartsCount || 0) + (section.tablesCount || 0);

          return (
            <button
              key={section.id}
              onClick={() => onSectionChange(section.id)}
              className={`w-full text-left px-3 py-2 rounded-md transition-all duration-200 ${
                isActive
                  ? 'bg-primary-dark text-white shadow-sm'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1 min-w-0">
                  {section.icon && (
                    <span className={`flex-shrink-0 ${isActive ? 'text-white' : 'text-gray-400'}`}>
                      {section.icon}
                    </span>
                  )}
                  <span className="font-medium text-sm truncate">{section.label}</span>
                </div>
                <ChevronRight
                  className={`w-4 h-4 flex-shrink-0 transition-transform ${
                    isActive ? 'translate-x-1' : ''
                  }`}
                />
              </div>

              {/* Counters */}
              {totalItems > 0 && (
                <div className="flex items-center space-x-3 mt-1 ml-6 text-xs">
                  {section.chartsCount ? (
                    <div className={`flex items-center space-x-1 ${isActive ? 'text-blue-200' : 'text-gray-500'}`}>
                      <BarChart3 className="w-3 h-3" />
                      <span>{section.chartsCount}</span>
                    </div>
                  ) : null}
                  {section.tablesCount ? (
                    <div className={`flex items-center space-x-1 ${isActive ? 'text-green-200' : 'text-gray-500'}`}>
                      <Table2 className="w-3 h-3" />
                      <span>{section.tablesCount}</span>
                    </div>
                  ) : null}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-600 space-y-1">
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1">
              <BarChart3 className="w-3 h-3" />
              <span>Graphiques</span>
            </span>
            <span className="font-semibold text-gray-900">
              {sections.reduce((sum, s) => sum + (s.chartsCount || 0), 0)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1">
              <Table2 className="w-3 h-3" />
              <span>Tableaux</span>
            </span>
            <span className="font-semibold text-gray-900">
              {sections.reduce((sum, s) => sum + (s.tablesCount || 0), 0)}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
