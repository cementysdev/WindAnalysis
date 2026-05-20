import { useState, useEffect, useMemo, type JSX } from 'react';
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

interface SectionData {
  charts: AnalyzeResponse['charts'];
  tables: AnalyzeResponse['tables'];
  loaded: boolean;
}

export function ScadaResults({ result }: ScadaResultsProps) {
  // État de la section active
  const [activeSection, setActiveSection] = useState<string>('summary');

  // État des sections chargées (lazy loading)
  const [loadedSections, setLoadedSections] = useState<Record<string, SectionData>>({});

  // Fonction pour charger les données d'une section à la demande
  const loadSectionData = (sectionId: string): SectionData => {
    // Si déjà chargée, retourner depuis le cache
    if (loadedSections[sectionId]?.loaded) {
      return loadedSections[sectionId];
    }

    let charts = result.charts;
    let tables = result.tables;

    // Filtrer selon la section
    switch (sectionId) {
      case 'eba':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('eba') || c.name.toLowerCase().includes('loss')
        );
        tables = result.tables.filter((t) => t.name.toLowerCase().includes('eba'));
        break;

      case 'tba':
        charts = result.charts.filter((c) => c.name.toLowerCase().includes('tba'));
        tables = result.tables.filter((t) => t.name.toLowerCase().includes('tba'));
        break;

      case 'error-codes':
        charts = result.charts.filter((c) => {
          const name = c.name.toLowerCase();
          return (
            name.includes('error_code') ||
            name.includes('top_error') ||
            name.includes('treemap_error') ||
            (name.includes('error') && name.includes('frequency')) ||
            (name.includes('code') && !name.includes('gps'))
          );
        });
        tables = result.tables.filter((t) => {
          const name = t.name.toLowerCase();
          return (
            name.includes('error') ||
            name.includes('code_pareto') ||
            (name.includes('code') && !name.includes('gps'))
          );
        });
        break;

      case 'data-availability':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('availability') || c.name.toLowerCase().includes('heatmap')
        );
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('availability')
        );
        break;

      case 'wind-direction':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('direction') || c.name.toLowerCase().includes('calibration')
        );
        tables = result.tables.filter((t) => t.name.toLowerCase().includes('direction'));
        break;

      case 'tip-speed':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('tip') || c.name.toLowerCase().includes('speed ratio')
        );
        tables = result.tables.filter((t) => t.name.toLowerCase().includes('tip'));
        break;

      case 'normative':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('normative') || c.name.toLowerCase().includes('yield')
        );
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('normative') || t.name.toLowerCase().includes('yield')
        );
        break;

      case 'wind-rose':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('wind_rose') && !c.name.toLowerCase().includes('power')
        );
        tables = [];
        break;

      case 'power-rose':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('power_rose') || (c.name.toLowerCase().includes('rose') && c.name.toLowerCase().includes('power'))
        );
        tables = [];
        break;

      case 'pitch':
        charts = result.charts.filter((c) => c.name.toLowerCase().includes('pitch'));
        tables = result.tables.filter((t) => t.name.toLowerCase().includes('pitch'));
        break;

      case 'performance':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('performance') && c.name.toLowerCase().includes('level')
        );
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('performance') && t.name.toLowerCase().includes('level')
        );
        break;

      case 'summary':
        charts = [];
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('summary') ||
          t.name.toLowerCase().includes('gps') ||
          t.name.toLowerCase().includes('coordinates')
        );
        break;

      case 'other':
        const categorizedChartNames = new Set(
          result.charts.filter((c) => {
            const name = c.name.toLowerCase();
            return (
              name.includes('eba') || name.includes('loss') || name.includes('tba') ||
              name.includes('error_code') || name.includes('top_error') || name.includes('treemap_error') ||
              (name.includes('error') && name.includes('frequency')) ||
              name.includes('availability') || name.includes('heatmap') ||
              name.includes('direction') || name.includes('calibration') ||
              name.includes('tip') || name.includes('speed ratio') ||
              name.includes('normative') || name.includes('yield') ||
              name.includes('wind_rose') || name.includes('power_rose') ||
              name.includes('pitch') ||
              (name.includes('performance') && name.includes('level'))
            );
          }).map((c) => c.name)
        );

        const categorizedTableNames = new Set(
          result.tables.filter((t) => {
            const name = t.name.toLowerCase();
            return (
              name.includes('eba') || name.includes('tba') ||
              name.includes('error') || name.includes('code_pareto') ||
              name.includes('availability') ||
              name.includes('direction') ||
              name.includes('tip') ||
              name.includes('normative') || name.includes('yield') ||
              name.includes('pitch') ||
              (name.includes('performance') && name.includes('level')) ||
              name.includes('summary') || name.includes('gps') || name.includes('coordinates')
            );
          }).map((t) => t.name)
        );

        charts = result.charts.filter((c) => !categorizedChartNames.has(c.name));
        tables = result.tables.filter((t) => !categorizedTableNames.has(t.name));
        break;

      default:
        charts = [];
        tables = [];
    }

    const sectionData: SectionData = { charts, tables, loaded: true };

    // Mettre en cache
    setLoadedSections((prev) => ({
      ...prev,
      [sectionId]: sectionData,
    }));

    return sectionData;
  };

  // Charger la section active quand elle change
  useEffect(() => {
    if (!loadedSections[activeSection]?.loaded) {
      loadSectionData(activeSection);
    }
  }, [activeSection]);

  // Obtenir les données de la section active (lazy loaded)
  const activeSectionData = useMemo(() => {
    return loadedSections[activeSection] || { charts: [], tables: [], loaded: false };
  }, [loadedSections, activeSection]);

  // Fonction helper pour compter rapidement les éléments d'une section
  // (sans charger les données complètes, juste pour la sidebar)
  const countSectionItems = (sectionId: string): { chartsCount: number; tablesCount: number } => {
    // Si déjà chargée, utiliser le cache
    if (loadedSections[sectionId]?.loaded) {
      return {
        chartsCount: loadedSections[sectionId].charts.length,
        tablesCount: loadedSections[sectionId].tables.length,
      };
    }

    // Sinon, calculer rapidement (filtre léger pour comptage uniquement)
    const data = loadSectionData(sectionId);
    return {
      chartsCount: data.charts.length,
      tablesCount: data.tables.length,
    };
  };

  // Build sidebar sections
  const sidebarSections: SidebarSection[] = [];

  const summaryCount = countSectionItems('summary');
  if (summaryCount.chartsCount > 0 || summaryCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'summary',
      label: 'Résumé',
      icon: <Info className="w-4 h-4" />,
      chartsCount: summaryCount.chartsCount,
      tablesCount: summaryCount.tablesCount,
    });
  }

  const ebaCount = countSectionItems('eba');
  if (ebaCount.chartsCount > 0 || ebaCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'eba',
      label: 'Analyse EBA',
      icon: <Zap className="w-4 h-4" />,
      chartsCount: ebaCount.chartsCount,
      tablesCount: ebaCount.tablesCount,
    });
  }

  const tbaCount = countSectionItems('tba');
  if (tbaCount.chartsCount > 0 || tbaCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'tba',
      label: 'Analyse TBA',
      icon: <Clock className="w-4 h-4" />,
      chartsCount: tbaCount.chartsCount,
      tablesCount: tbaCount.tablesCount,
    });
  }

  const errorCodesCount = countSectionItems('error-codes');
  if (errorCodesCount.chartsCount > 0 || errorCodesCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'error-codes',
      label: 'Codes d\'erreur',
      icon: <AlertTriangle className="w-4 h-4" />,
      chartsCount: errorCodesCount.chartsCount,
      tablesCount: errorCodesCount.tablesCount,
    });
  }

  const dataAvailabilityCount = countSectionItems('data-availability');
  if (dataAvailabilityCount.chartsCount > 0 || dataAvailabilityCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'data-availability',
      label: 'Disponibilité données',
      icon: <Database className="w-4 h-4" />,
      chartsCount: dataAvailabilityCount.chartsCount,
      tablesCount: dataAvailabilityCount.tablesCount,
    });
  }

  const windDirectionCount = countSectionItems('wind-direction');
  if (windDirectionCount.chartsCount > 0 || windDirectionCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'wind-direction',
      label: 'Calibration vent',
      icon: <Compass className="w-4 h-4" />,
      chartsCount: windDirectionCount.chartsCount,
      tablesCount: windDirectionCount.tablesCount,
    });
  }

  const windRoseCount = countSectionItems('wind-rose');
  if (windRoseCount.chartsCount > 0 || windRoseCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'wind-rose',
      label: 'Rose des vents',
      icon: <Wind className="w-4 h-4" />,
      chartsCount: windRoseCount.chartsCount,
      tablesCount: windRoseCount.tablesCount,
    });
  }

  const powerRoseCount = countSectionItems('power-rose');
  if (powerRoseCount.chartsCount > 0 || powerRoseCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'power-rose',
      label: 'Rose des puissances',
      icon: <TrendingUp className="w-4 h-4" />,
      chartsCount: powerRoseCount.chartsCount,
      tablesCount: powerRoseCount.tablesCount,
    });
  }

  const tipSpeedCount = countSectionItems('tip-speed');
  if (tipSpeedCount.chartsCount > 0 || tipSpeedCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'tip-speed',
      label: 'Tip Speed Ratio',
      icon: <Gauge className="w-4 h-4" />,
      chartsCount: tipSpeedCount.chartsCount,
      tablesCount: tipSpeedCount.tablesCount,
    });
  }

  const normativeCount = countSectionItems('normative');
  if (normativeCount.chartsCount > 0 || normativeCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'normative',
      label: 'Analyse normative',
      icon: <Activity className="w-4 h-4" />,
      chartsCount: normativeCount.chartsCount,
      tablesCount: normativeCount.tablesCount,
    });
  }

  const pitchCount = countSectionItems('pitch');
  if (pitchCount.chartsCount > 0 || pitchCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'pitch',
      label: 'Analyse Pitch',
      icon: <Settings className="w-4 h-4" />,
      chartsCount: pitchCount.chartsCount,
      tablesCount: pitchCount.tablesCount,
    });
  }

  const performanceCount = countSectionItems('performance');
  if (performanceCount.chartsCount > 0 || performanceCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'performance',
      label: 'Performance Level',
      icon: <TrendingUp className="w-4 h-4" />,
      chartsCount: performanceCount.chartsCount,
      tablesCount: performanceCount.tablesCount,
    });
  }

  const otherCount = countSectionItems('other');
  if (otherCount.chartsCount > 0 || otherCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'other',
      label: 'Autres',
      icon: <Activity className="w-4 h-4" />,
      chartsCount: otherCount.chartsCount,
      tablesCount: otherCount.tablesCount,
    });
  }

  // Fonction helper pour rendre une section avec charts et tables
  const renderSection = (title: string, icon: typeof Zap): JSX.Element => {
    const { charts, tables } = activeSectionData;

    return (
      <CategoryCard title={title} icon={icon} defaultOpen={true}>
        <div className="space-y-6">
          {charts.map((chart: AnalyzeResponse['charts'][0], idx: number) => (
            <div key={idx} className="mb-6">
              <ChartViewer charts={[chart]} />
            </div>
          ))}
          {tables.map((table: AnalyzeResponse['tables'][0], idx: number) => (
            <div key={idx} className="mt-6">
              <h4 className="text-md font-semibold mb-3">{table.name}</h4>
              <PaginatedTable table={table} itemsPerPage={10} />
            </div>
          ))}
        </div>
      </CategoryCard>
    );
  };

  // Section content map - render only active section (lazy loaded)
  const sectionContentMap: Record<string, JSX.Element> = {
    'summary': renderSection('Résumé du Parc', Info),
    'eba': renderSection('Analyse EBA (Energy-Based Availability)', Zap),
    'tba': renderSection('Analyse TBA (Time-Based Availability)', Clock),
    'error-codes': renderSection('Analyse des codes d\'erreur', AlertTriangle),
    'data-availability': renderSection('Disponibilité des données', Database),
    'wind-direction': renderSection('Calibration de la direction du vent', Compass),
    'tip-speed': renderSection('Tip Speed Ratio', Gauge),
    'normative': renderSection('Analyse normative IEC', Activity),
    'wind-rose': renderSection('Rose des vents', Wind),
    'power-rose': renderSection('Rose des puissances', TrendingUp),
    'pitch': renderSection('Analyse Pitch', Settings),
    'performance': renderSection('Performance Level', TrendingUp),
    'other': renderSection('Autres résultats', Activity),
  };

  return (
    <div className="flex gap-6">
      {/* Sidebar */}
      <ResultsSidebar
        sections={sidebarSections}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* Main Content - Render only active section */}
      <div className="flex-1">
        {sectionContentMap[activeSection] || (
          <div className="text-center text-gray-500 py-8">
            Section non trouvée
          </div>
        )}

        {/* Download Report - Always visible at bottom */}
        <div className="mt-6">
          <CategoryCard title="Téléchargement" icon={Zap} defaultOpen={true} collapsible={false}>
            <DownloadButton reportPath={result.report_path} />
          </CategoryCard>
        </div>
      </div>
    </div>
  );
}
