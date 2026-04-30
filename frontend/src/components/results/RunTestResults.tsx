import type { AnalyzeResponse } from '../../types/analysis';
import { CategoryCard } from '../shared/CategoryCard';
import { PaginatedTable } from '../shared/PaginatedTable';
import { ChartViewer } from '../ChartViewer';
import { DownloadButton } from '../shared/DownloadButton';
import { CheckCircle, Clock, Zap, RotateCcw, Activity, Wind } from 'lucide-react';

interface RunTestResultsProps {
  result: AnalyzeResponse;
}

function ValidationSummary({ result }: { result: AnalyzeResponse }) {
  // Extract validation status from metadata or tables
  const criteria = result.metadata?.criteria || {};

  const criteriaItems = [
    { key: 'consecutive_hours', label: '120 heures consécutives', icon: Clock },
    { key: 'test_cut_in_cut_out', label: 'Cut-In à Cut-Out', icon: Activity },
    { key: 'nominal_power', label: 'Puissance nominale', icon: Zap },
    { key: 'local_restarts', label: 'Redémarrages locaux', icon: RotateCcw },
    { key: 'availability', label: 'Disponibilité', icon: CheckCircle },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {criteriaItems.map((item) => {
        const criterion = criteria[item.key];

        return (
          <div
            key={item.key}
            className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-900">{item.label}</p>
              {criterion && (
                <p className="text-xs text-gray-600">
                  Critère: {criterion.value} {criterion.unit}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RunTestResults({ result }: RunTestResultsProps) {
  // Group charts and tables by category
  const consecutiveHoursCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('consecutive') && !c.name.toLowerCase().includes('heatmap')
  );
  const consecutiveHoursTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('consecutive')
  );

  const cutInOutCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('cut') || c.name.toLowerCase().includes('power')
  );
  const cutInOutTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('cut')
  );

  const nominalPowerCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('nominal')
  );
  const nominalPowerTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('nominal')
  );

  const restartsTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('restart') || t.name.toLowerCase().includes('autonomous')
  );

  const availabilityTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('availability') || t.name.toLowerCase().includes('disponibilit')
  );

  // Wind Rose Charts
  const windRoseCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('wind_rose') || c.name.toLowerCase().includes('rose_chart')
  );

  // Summary table (first table usually)
  const summaryTable = result.tables.find((t) =>
    t.name.toLowerCase().includes('summary') || t.name.toLowerCase().includes('résumé')
  ) || result.tables[0];

  return (
    <div className="space-y-6">
      {/* Validation Summary */}
      <CategoryCard title="Résumé de validation" icon={CheckCircle} defaultOpen={true}>
        <ValidationSummary result={result} />
      </CategoryCard>

      {/* Summary Table */}
      {summaryTable && (
        <CategoryCard title={summaryTable.name} icon={Activity} defaultOpen={true}>
          <PaginatedTable table={summaryTable} itemsPerPage={10} />
        </CategoryCard>
      )}

      {/* 120 Consecutive Hours */}
      {(consecutiveHoursCharts.length > 0 || consecutiveHoursTables.length > 0) && (
        <CategoryCard title="120 heures consécutives" icon={Clock} defaultOpen={true}>
          <div className="space-y-6">
            {consecutiveHoursCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {consecutiveHoursTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Cut-In to Cut-Out */}
      {(cutInOutCharts.length > 0 || cutInOutTables.length > 0) && (
        <CategoryCard title="Test Cut-In à Cut-Out" icon={Activity} defaultOpen={true}>
          <div className="space-y-6">
            {cutInOutCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {cutInOutTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Nominal Power */}
      {(nominalPowerCharts.length > 0 || nominalPowerTables.length > 0) && (
        <CategoryCard title="Puissance nominale" icon={Zap} defaultOpen={true}>
          <div className="space-y-6">
            {nominalPowerCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {nominalPowerTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Local Restarts */}
      {restartsTables.length > 0 && (
        <CategoryCard title="Redémarrages locaux" icon={RotateCcw} defaultOpen={true}>
          <div className="space-y-4">
            {restartsTables.map((table, idx) => (
              <div key={idx}>
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Availability */}
      {availabilityTables.length > 0 && (
        <CategoryCard title="Disponibilité" icon={CheckCircle} defaultOpen={true}>
          <div className="space-y-4">
            {availabilityTables.map((table, idx) => (
              <div key={idx}>
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Wind Rose */}
      {windRoseCharts.length > 0 && (
        <CategoryCard title="Rose des vents" icon={Wind} defaultOpen={true}>
          <div className="space-y-6">
            {windRoseCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Download Report */}
      <CategoryCard title="Téléchargement" icon={CheckCircle} defaultOpen={true} collapsible={false}>
        <DownloadButton reportPath={result.report_path} />
      </CategoryCard>
    </div>
  );
}
