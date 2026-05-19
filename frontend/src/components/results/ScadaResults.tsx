import type { AnalyzeResponse } from '../../types/analysis';
import { CategoryCard } from '../shared/CategoryCard';
import { PaginatedTable } from '../shared/PaginatedTable';
import { ChartViewer } from '../ChartViewer';
import { DownloadButton } from '../shared/DownloadButton';
import { ResultsSidebar, type SidebarSection } from './ResultsSidebar';
import { Zap, AlertTriangle, Database, Wind, Gauge, TrendingUp, Compass, Clock, Settings, Activity, Info } from 'lucide-react';

interface ScadaResultsProps {
  result: AnalyzeResponse;
}

export function ScadaResults({ result }: ScadaResultsProps) {
  // Group charts and tables by category
  const ebaCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('eba') || c.name.toLowerCase().includes('loss')
  );
  const ebaTables = result.tables.filter((t) => t.name.toLowerCase().includes('eba'));

  const errorCodeCharts = result.charts.filter((c) => {
    const name = c.name.toLowerCase();
    return (
      name.includes('error_code') ||
      name.includes('top_error') ||
      name.includes('treemap_error') ||
      (name.includes('error') && name.includes('frequency')) ||
      (name.includes('code') && !name.includes('gps'))
    );
  });
  const errorCodeTables = result.tables.filter((t) => {
    const name = t.name.toLowerCase();
    return (
      name.includes('error') ||
      name.includes('code_pareto') ||
      (name.includes('code') && !name.includes('gps'))
    );
  });

  const dataAvailabilityCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('availability') || c.name.toLowerCase().includes('heatmap')
  );
  const dataAvailabilityTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('availability')
  );

  const windDirectionCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('direction') || c.name.toLowerCase().includes('calibration')
  );
  const windDirectionTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('direction')
  );

  const tipSpeedCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('tip') || c.name.toLowerCase().includes('speed ratio')
  );
  const tipSpeedTables = result.tables.filter((t) => t.name.toLowerCase().includes('tip'));

  const normativeCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('normative') || c.name.toLowerCase().includes('yield')
  );
  const normativeTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('normative') || t.name.toLowerCase().includes('yield')
  );

  // Wind Rose Charts
  const windRoseCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('wind_rose') && !c.name.toLowerCase().includes('power')
  );

  // Power Rose Charts
  const powerRoseCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('power_rose') || c.name.toLowerCase().includes('rose') && c.name.toLowerCase().includes('power')
  );

  // TBA Analysis
  const tbaCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('tba')
  );
  const tbaTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('tba')
  );

  // Pitch Analysis
  const pitchCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('pitch')
  );
  const pitchTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('pitch')
  );

  // Performance Level
  const performanceCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('performance') && c.name.toLowerCase().includes('level')
  );
  const performanceTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('performance') && t.name.toLowerCase().includes('level')
  );

  // Summary Section
  const summaryTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('summary') ||
    t.name.toLowerCase().includes('gps') ||
    t.name.toLowerCase().includes('coordinates')
  );

  // Remaining charts/tables not categorized
  const categorizedChartNames = new Set([
    ...ebaCharts,
    ...tbaCharts,
    ...errorCodeCharts,
    ...dataAvailabilityCharts,
    ...windDirectionCharts,
    ...tipSpeedCharts,
    ...normativeCharts,
    ...windRoseCharts,
    ...powerRoseCharts,
    ...pitchCharts,
    ...performanceCharts,
  ].map((c) => c.name));

  const otherCharts = result.charts.filter((c) => !categorizedChartNames.has(c.name));

  const categorizedTableNames = new Set([
    ...ebaTables,
    ...tbaTables,
    ...errorCodeTables,
    ...dataAvailabilityTables,
    ...windDirectionTables,
    ...tipSpeedTables,
    ...normativeTables,
    ...pitchTables,
    ...performanceTables,
    ...summaryTables,
  ].map((t) => t.name));

  const otherTables = result.tables.filter((t) => !categorizedTableNames.has(t.name));

  // Build sidebar sections
  const sidebarSections: SidebarSection[] = [];

  if (summaryTables.length > 0) {
    sidebarSections.push({
      id: 'summary',
      label: 'Résumé',
      icon: <Info className="w-4 h-4" />,
      chartsCount: 0,
      tablesCount: summaryTables.length,
    });
  }

  if (ebaCharts.length > 0 || ebaTables.length > 0) {
    sidebarSections.push({
      id: 'eba',
      label: 'Analyse EBA',
      icon: <Zap className="w-4 h-4" />,
      chartsCount: ebaCharts.length,
      tablesCount: ebaTables.length,
    });
  }

  if (tbaCharts.length > 0 || tbaTables.length > 0) {
    sidebarSections.push({
      id: 'tba',
      label: 'Analyse TBA',
      icon: <Clock className="w-4 h-4" />,
      chartsCount: tbaCharts.length,
      tablesCount: tbaTables.length,
    });
  }

  if (errorCodeCharts.length > 0 || errorCodeTables.length > 0) {
    sidebarSections.push({
      id: 'error-codes',
      label: 'Codes d\'erreur',
      icon: <AlertTriangle className="w-4 h-4" />,
      chartsCount: errorCodeCharts.length,
      tablesCount: errorCodeTables.length,
    });
  }

  if (dataAvailabilityCharts.length > 0 || dataAvailabilityTables.length > 0) {
    sidebarSections.push({
      id: 'data-availability',
      label: 'Disponibilité données',
      icon: <Database className="w-4 h-4" />,
      chartsCount: dataAvailabilityCharts.length,
      tablesCount: dataAvailabilityTables.length,
    });
  }

  if (windDirectionCharts.length > 0 || windDirectionTables.length > 0) {
    sidebarSections.push({
      id: 'wind-direction',
      label: 'Calibration vent',
      icon: <Compass className="w-4 h-4" />,
      chartsCount: windDirectionCharts.length,
      tablesCount: windDirectionTables.length,
    });
  }

  if (windRoseCharts.length > 0) {
    sidebarSections.push({
      id: 'wind-rose',
      label: 'Rose des vents',
      icon: <Wind className="w-4 h-4" />,
      chartsCount: windRoseCharts.length,
      tablesCount: 0,
    });
  }

  if (powerRoseCharts.length > 0) {
    sidebarSections.push({
      id: 'power-rose',
      label: 'Rose des puissances',
      icon: <TrendingUp className="w-4 h-4" />,
      chartsCount: powerRoseCharts.length,
      tablesCount: 0,
    });
  }

  if (tipSpeedCharts.length > 0 || tipSpeedTables.length > 0) {
    sidebarSections.push({
      id: 'tip-speed',
      label: 'Tip Speed Ratio',
      icon: <Gauge className="w-4 h-4" />,
      chartsCount: tipSpeedCharts.length,
      tablesCount: tipSpeedTables.length,
    });
  }

  if (normativeCharts.length > 0 || normativeTables.length > 0) {
    sidebarSections.push({
      id: 'normative',
      label: 'Rendement normatif',
      icon: <Activity className="w-4 h-4" />,
      chartsCount: normativeCharts.length,
      tablesCount: normativeTables.length,
    });
  }

  if (pitchCharts.length > 0 || pitchTables.length > 0) {
    sidebarSections.push({
      id: 'pitch',
      label: 'Analyse Pitch',
      icon: <Settings className="w-4 h-4" />,
      chartsCount: pitchCharts.length,
      tablesCount: pitchTables.length,
    });
  }

  if (performanceCharts.length > 0 || performanceTables.length > 0) {
    sidebarSections.push({
      id: 'performance',
      label: 'Performance niveau',
      icon: <TrendingUp className="w-4 h-4" />,
      chartsCount: performanceCharts.length,
      tablesCount: performanceTables.length,
    });
  }

  if (otherCharts.length > 0 || otherTables.length > 0) {
    sidebarSections.push({
      id: 'other',
      label: 'Autres résultats',
      icon: <Database className="w-4 h-4" />,
      chartsCount: otherCharts.length,
      tablesCount: otherTables.length,
    });
  }

  return (
    <div className="flex gap-6">
      {/* Sidebar */}
      <ResultsSidebar sections={sidebarSections} />

      {/* Main Content */}
      <div className="flex-1 space-y-6">
      {/* Summary Section */}
      {summaryTables.length > 0 && (
        <div id="summary">
          <CategoryCard title="Résumé du Parc" icon={Info} defaultOpen={true}>
          <div className="space-y-6">
            {summaryTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* EBA Analysis */}
      {(ebaCharts.length > 0 || ebaTables.length > 0) && (
        <div id="eba">
          <CategoryCard title="Analyse EBA (Energy-Based Availability)" icon={Zap} defaultOpen={true}>
            <div className="space-y-6">
              {ebaCharts.map((chart, idx) => (
                <div key={idx} className="mb-6">
                  <ChartViewer charts={[chart]} />
                </div>
              ))}
              {ebaTables.map((table, idx) => (
                <div key={idx} className="mt-6">
                  <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                  <PaginatedTable table={table} itemsPerPage={10} />
                </div>
              ))}
            </div>
          </CategoryCard>
        </div>
      )}

      {/* TBA Analysis */}
      {(tbaCharts.length > 0 || tbaTables.length > 0) && (
        <div id="tba">
          <CategoryCard title="Analyse TBA (Time-Based Availability)" icon={Clock} defaultOpen={true}>
          <div className="space-y-6">
            {tbaCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {tbaTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Error Code Analysis */}
      {(errorCodeCharts.length > 0 || errorCodeTables.length > 0) && (
        <div id="error-codes">
          <CategoryCard title="Analyse des codes d'erreur" icon={AlertTriangle} defaultOpen={true}>
          <div className="space-y-6">
            {errorCodeCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {errorCodeTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Data Availability */}
      {(dataAvailabilityCharts.length > 0 || dataAvailabilityTables.length > 0) && (
        <div id="data-availability">
          <CategoryCard title="Disponibilité des données" icon={Database} defaultOpen={true}>
          <div className="space-y-6">
            {dataAvailabilityCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {dataAvailabilityTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Wind Direction Calibration */}
      {(windDirectionCharts.length > 0 || windDirectionTables.length > 0) && (
        <div id="wind-direction">
          <CategoryCard title="Calibration de la direction du vent" icon={Wind} defaultOpen={true}>
          <div className="space-y-6">
            {windDirectionCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {windDirectionTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Tip Speed Ratio */}
      {(tipSpeedCharts.length > 0 || tipSpeedTables.length > 0) && (
        <div id="tip-speed">
          <CategoryCard title="Tip Speed Ratio" icon={Gauge} defaultOpen={true}>
          <div className="space-y-6">
            {tipSpeedCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {tipSpeedTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Normative Yield */}
      {(normativeCharts.length > 0 || normativeTables.length > 0) && (
        <div id="normative">
          <CategoryCard title="Rendement normatif (IEC 61400-12-2)" icon={TrendingUp} defaultOpen={true}>
          <div className="space-y-6">
            {normativeCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {normativeTables.map((table, idx) => (
              <div key={idx} className="mt-6">
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

      {/* Power Rose */}
      {powerRoseCharts.length > 0 && (
        <div id="power-rose">
          <CategoryCard title="Rose de puissance" icon={Compass} defaultOpen={true}>
          <div className="space-y-6">
            {powerRoseCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Pitch Analysis */}
      {(pitchCharts.length > 0 || pitchTables.length > 0) && (
        <div id="pitch">
          <CategoryCard title="Analyse du Pitch" icon={Settings} defaultOpen={true}>
          <div className="space-y-6">
            {pitchCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {pitchTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Performance Level */}
      {(performanceCharts.length > 0 || performanceTables.length > 0) && (
        <div id="performance">
          <CategoryCard title="Niveau de Performance (Classification des Zones)" icon={Activity} defaultOpen={true}>
          <div className="space-y-6">
            {performanceCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {performanceTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Other Results */}
      {(otherCharts.length > 0 || otherTables.length > 0) && (
        <div id="other">
          <CategoryCard title="Autres résultats" icon={Database} defaultOpen={false}>
          <div className="space-y-6">
            {otherCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
            {otherTables.map((table, idx) => (
              <div key={idx} className="mt-6">
                <h4 className="text-md font-semibold mb-3">{table.name}</h4>
                <PaginatedTable table={table} itemsPerPage={10} />
              </div>
            ))}
          </div>
        </CategoryCard>
        </div>
      )}

      {/* Download Report */}
      <CategoryCard title="Téléchargement" icon={Zap} defaultOpen={true} collapsible={false}>
        <DownloadButton reportPath={result.report_path} />
      </CategoryCard>
    </div>
    </div>
  );
}
