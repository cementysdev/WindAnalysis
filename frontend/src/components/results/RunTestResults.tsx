import type { AnalyzeResponse } from '../../types/analysis';
import { CategoryCard } from '../shared/CategoryCard';
import { PaginatedTable } from '../shared/PaginatedTable';
import { ChartViewer } from '../ChartViewer';
import { DownloadButton } from '../shared/DownloadButton';
import { ResultsSidebar, type SidebarSection } from './ResultsSidebar';
import { CheckCircle, Clock, Zap, RotateCcw, Activity, Wind, BarChart3, Info } from 'lucide-react';

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

  // Wind Histogram Charts
  const windHistogramCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('wind_histogram') || c.name.toLowerCase().includes('histogram_chart')
  );

  // Timeline Charts
  const timelineCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('timeline')
  );

  // Power Curve Charts
  const powerCurveCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('power_curve') || c.name.toLowerCase().includes('courbe')
  );

  // Summary table (first table usually)
  const summaryTable = result.tables.find((t) =>
    t.name.toLowerCase().includes('summary') || t.name.toLowerCase().includes('résumé')
  ) || result.tables[0];

  // Build sidebar sections
  const sidebarSections: SidebarSection[] = [];

  // Validation Summary
  sidebarSections.push({
    id: 'validation',
    label: 'Résumé de validation',
    icon: <CheckCircle className="w-4 h-4" />,
    chartsCount: 0,
    tablesCount: 0,
  });

  // Summary Table
  if (summaryTable) {
    sidebarSections.push({
      id: 'summary',
      label: 'Tableau récapitulatif',
      icon: <Info className="w-4 h-4" />,
      chartsCount: 0,
      tablesCount: 1,
    });
  }

  // 120 Consecutive Hours
  if (consecutiveHoursCharts.length > 0 || consecutiveHoursTables.length > 0) {
    sidebarSections.push({
      id: 'consecutive',
      label: '120h consécutives',
      icon: <Clock className="w-4 h-4" />,
      chartsCount: consecutiveHoursCharts.length,
      tablesCount: consecutiveHoursTables.length,
    });
  }

  // Cut-In to Cut-Out (includes timeline)
  if (cutInOutCharts.length > 0 || cutInOutTables.length > 0 || timelineCharts.length > 0) {
    sidebarSections.push({
      id: 'cutinout',
      label: 'Cut-In à Cut-Out',
      icon: <Activity className="w-4 h-4" />,
      chartsCount: cutInOutCharts.length + timelineCharts.length,
      tablesCount: cutInOutTables.length,
    });
  }

  // Nominal Power
  if (nominalPowerCharts.length > 0 || nominalPowerTables.length > 0) {
    sidebarSections.push({
      id: 'nominal',
      label: 'Puissance nominale',
      icon: <Zap className="w-4 h-4" />,
      chartsCount: nominalPowerCharts.length,
      tablesCount: nominalPowerTables.length,
    });
  }

  // Local Restarts
  if (restartsTables.length > 0) {
    sidebarSections.push({
      id: 'restarts',
      label: 'Redémarrages locaux',
      icon: <RotateCcw className="w-4 h-4" />,
      chartsCount: 0,
      tablesCount: restartsTables.length,
    });
  }

  // Availability
  if (availabilityTables.length > 0) {
    sidebarSections.push({
      id: 'availability',
      label: 'Disponibilité',
      icon: <CheckCircle className="w-4 h-4" />,
      chartsCount: 0,
      tablesCount: availabilityTables.length,
    });
  }

  // Wind Rose
  if (windRoseCharts.length > 0) {
    sidebarSections.push({
      id: 'wind-rose',
      label: 'Rose des vents',
      icon: <Wind className="w-4 h-4" />,
      chartsCount: windRoseCharts.length,
      tablesCount: 0,
    });
  }

  // Wind Histogram
  if (windHistogramCharts.length > 0) {
    sidebarSections.push({
      id: 'wind-histogram',
      label: 'Distribution vent',
      icon: <BarChart3 className="w-4 h-4" />,
      chartsCount: windHistogramCharts.length,
      tablesCount: 0,
    });
  }


  // Power Curve
  if (powerCurveCharts.length > 0) {
    sidebarSections.push({
      id: 'power-curve',
      label: 'Courbe de puissance',
      icon: <Zap className="w-4 h-4" />,
      chartsCount: powerCurveCharts.length,
      tablesCount: 0,
    });
  }

  return (
    <div className="flex gap-6">
      {/* Sidebar */}
      <ResultsSidebar sections={sidebarSections} />

      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Validation Summary */}
        <div id="validation">
          <CategoryCard title="Résumé de validation" icon={CheckCircle} defaultOpen={true}>
            <ValidationSummary result={result} />
          </CategoryCard>
        </div>

        {/* Summary Table */}
        {summaryTable && (
          <div id="summary">
            <CategoryCard title={summaryTable.name} icon={Activity} defaultOpen={true}>
              <PaginatedTable table={summaryTable} itemsPerPage={10} />
            </CategoryCard>
          </div>
        )}

        {/* 120 Consecutive Hours */}
        {(consecutiveHoursCharts.length > 0 || consecutiveHoursTables.length > 0) && (
          <div id="consecutive">
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
          </div>
        )}

        {/* Cut-In to Cut-Out */}
        {(cutInOutCharts.length > 0 || cutInOutTables.length > 0 || timelineCharts.length > 0) && (
          <div id="cutinout">
            <CategoryCard title="Test Cut-In à Cut-Out" icon={Activity} defaultOpen={true}>
              <div className="space-y-6">
                {cutInOutCharts.map((chart, idx) => (
                  <div key={idx} className="mb-6">
                    <ChartViewer charts={[chart]} />
                  </div>
                ))}
                {timelineCharts.map((chart, idx) => (
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
          </div>
        )}

        {/* Nominal Power */}
        {(nominalPowerCharts.length > 0 || nominalPowerTables.length > 0) && (
          <div id="nominal">
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
          </div>
        )}

        {/* Local Restarts */}
        {restartsTables.length > 0 && (
          <div id="restarts">
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
          </div>
        )}

        {/* Availability */}
        {availabilityTables.length > 0 && (
          <div id="availability">
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
          </div>
        )}

        {/* Wind Rose */}
        {windRoseCharts.length > 0 && (
          <div id="wind-rose">
            <CategoryCard title="Rose des vents" icon={Wind} defaultOpen={true}>
              <div className="space-y-6">
                {windRoseCharts.map((chart, idx) => (
                  <div key={idx} className="mb-6">
                    <ChartViewer charts={[chart]} />
                  </div>
                ))}
              </div>
            </CategoryCard>
          </div>
        )}

        {/* Wind Histogram */}
        {windHistogramCharts.length > 0 && (
          <div id="wind-histogram">
            <CategoryCard title="Distribution de la vitesse du vent" icon={BarChart3} defaultOpen={true}>
              <div className="space-y-6">
                {windHistogramCharts.map((chart, idx) => (
                  <div key={idx} className="mb-6">
                    <ChartViewer charts={[chart]} />
                  </div>
                ))}
              </div>
            </CategoryCard>
          </div>
        )}

        {/* Power Curve */}
        {powerCurveCharts.length > 0 && (
          <div id="power-curve">
            <CategoryCard title="Courbe de puissance" icon={Zap} defaultOpen={true}>
              <div className="space-y-6">
                {powerCurveCharts.map((chart, idx) => (
                  <div key={idx} className="mb-6">
                    <ChartViewer charts={[chart]} />
                  </div>
                ))}
              </div>
            </CategoryCard>
          </div>
        )}

        {/* Download Report */}
        <CategoryCard title="Téléchargement" icon={CheckCircle} defaultOpen={true} collapsible={false}>
          <DownloadButton reportPath={result.report_path} />
        </CategoryCard>
      </div>
    </div>
  );
}
