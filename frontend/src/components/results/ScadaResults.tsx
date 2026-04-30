import type { AnalyzeResponse } from '../../types/analysis';
import { CategoryCard } from '../shared/CategoryCard';
import { PaginatedTable } from '../shared/PaginatedTable';
import { ChartViewer } from '../ChartViewer';
import { DownloadButton } from '../shared/DownloadButton';
import { Zap, AlertTriangle, Database, Wind, Gauge, TrendingUp, Compass } from 'lucide-react';

interface ScadaResultsProps {
  result: AnalyzeResponse;
}

export function ScadaResults({ result }: ScadaResultsProps) {
  // Group charts and tables by category
  const ebaCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('eba') || c.name.toLowerCase().includes('loss')
  );
  const ebaTables = result.tables.filter((t) => t.name.toLowerCase().includes('eba'));

  const errorCodeCharts = result.charts.filter((c) =>
    c.name.toLowerCase().includes('error') || c.name.toLowerCase().includes('code')
  );
  const errorCodeTables = result.tables.filter((t) =>
    t.name.toLowerCase().includes('error') || t.name.toLowerCase().includes('code')
  );

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

  // Remaining charts/tables not categorized
  const categorizedChartNames = new Set([
    ...ebaCharts,
    ...errorCodeCharts,
    ...dataAvailabilityCharts,
    ...windDirectionCharts,
    ...tipSpeedCharts,
    ...normativeCharts,
    ...windRoseCharts,
    ...powerRoseCharts,
  ].map((c) => c.name));

  const otherCharts = result.charts.filter((c) => !categorizedChartNames.has(c.name));

  const categorizedTableNames = new Set([
    ...ebaTables,
    ...errorCodeTables,
    ...dataAvailabilityTables,
    ...windDirectionTables,
    ...tipSpeedTables,
    ...normativeTables,
  ].map((t) => t.name));

  const otherTables = result.tables.filter((t) => !categorizedTableNames.has(t.name));

  return (
    <div className="space-y-6">
      {/* EBA Analysis */}
      {(ebaCharts.length > 0 || ebaTables.length > 0) && (
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
      )}

      {/* Error Code Analysis */}
      {(errorCodeCharts.length > 0 || errorCodeTables.length > 0) && (
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
      )}

      {/* Data Availability */}
      {(dataAvailabilityCharts.length > 0 || dataAvailabilityTables.length > 0) && (
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
      )}

      {/* Wind Direction Calibration */}
      {(windDirectionCharts.length > 0 || windDirectionTables.length > 0) && (
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
      )}

      {/* Tip Speed Ratio */}
      {(tipSpeedCharts.length > 0 || tipSpeedTables.length > 0) && (
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
      )}

      {/* Normative Yield */}
      {(normativeCharts.length > 0 || normativeTables.length > 0) && (
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

      {/* Power Rose */}
      {powerRoseCharts.length > 0 && (
        <CategoryCard title="Rose de puissance" icon={Compass} defaultOpen={true}>
          <div className="space-y-6">
            {powerRoseCharts.map((chart, idx) => (
              <div key={idx} className="mb-6">
                <ChartViewer charts={[chart]} />
              </div>
            ))}
          </div>
        </CategoryCard>
      )}

      {/* Other Results */}
      {(otherCharts.length > 0 || otherTables.length > 0) && (
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
      )}

      {/* Download Report */}
      <CategoryCard title="Téléchargement" icon={Zap} defaultOpen={true} collapsible={false}>
        <DownloadButton reportPath={result.report_path} />
      </CategoryCard>
    </div>
  );
}
