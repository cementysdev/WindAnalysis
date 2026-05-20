import { useState, useEffect, useMemo, type JSX } from 'react';
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

interface SectionData {
  charts: AnalyzeResponse['charts'];
  tables: AnalyzeResponse['tables'];
  loaded: boolean;
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
  // État de la section active
  const [activeSection, setActiveSection] = useState<string>('validation');

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
      case 'validation':
        charts = [];
        tables = [];
        break;

      case 'summary':
        charts = [];
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('summary') || t.name.toLowerCase().includes('résumé')
        );
        break;

      case 'consecutive':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('consecutive') && !c.name.toLowerCase().includes('heatmap')
        );
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('consecutive')
        );
        break;

      case 'cutinout':
        const cutInOutCharts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('cut') || c.name.toLowerCase().includes('power')
        );
        const timelineCharts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('timeline')
        );
        charts = [...cutInOutCharts, ...timelineCharts];
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('cut')
        );
        break;

      case 'nominal':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('nominal')
        );
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('nominal')
        );
        break;

      case 'restarts':
        charts = [];
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('restart') || t.name.toLowerCase().includes('autonomous')
        );
        break;

      case 'availability':
        charts = [];
        tables = result.tables.filter((t) =>
          t.name.toLowerCase().includes('availability') || t.name.toLowerCase().includes('disponibilit')
        );
        break;

      case 'wind-rose':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('wind_rose') || c.name.toLowerCase().includes('rose_chart')
        );
        tables = [];
        break;

      case 'wind-histogram':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('wind_histogram') || c.name.toLowerCase().includes('histogram_chart')
        );
        tables = [];
        break;

      case 'power-curve':
        charts = result.charts.filter((c) =>
          c.name.toLowerCase().includes('power_curve') || c.name.toLowerCase().includes('courbe')
        );
        tables = [];
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
  }, [activeSection, loadedSections]);

  // Obtenir les données de la section active (lazy loaded)
  const activeSectionData = useMemo(() => {
    return loadedSections[activeSection] || { charts: [], tables: [], loaded: false };
  }, [loadedSections, activeSection]);

  // Fonction helper pour compter rapidement les éléments d'une section
  const countSectionItems = (sectionId: string): { chartsCount: number; tablesCount: number } => {
    if (loadedSections[sectionId]?.loaded) {
      return {
        chartsCount: loadedSections[sectionId].charts.length,
        tablesCount: loadedSections[sectionId].tables.length,
      };
    }

    const data = loadSectionData(sectionId);
    return {
      chartsCount: data.charts.length,
      tablesCount: data.tables.length,
    };
  };

  // Build sidebar sections
  const sidebarSections: SidebarSection[] = [];

  // Validation Summary - always visible
  sidebarSections.push({
    id: 'validation',
    label: 'Résumé de validation',
    icon: <CheckCircle className="w-4 h-4" />,
    chartsCount: 0,
    tablesCount: 0,
  });

  // Summary Table
  const summaryCount = countSectionItems('summary');
  if (summaryCount.chartsCount > 0 || summaryCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'summary',
      label: 'Tableau récapitulatif',
      icon: <Info className="w-4 h-4" />,
      chartsCount: summaryCount.chartsCount,
      tablesCount: summaryCount.tablesCount,
    });
  }

  // 120 Consecutive Hours
  const consecutiveCount = countSectionItems('consecutive');
  if (consecutiveCount.chartsCount > 0 || consecutiveCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'consecutive',
      label: '120h consécutives',
      icon: <Clock className="w-4 h-4" />,
      chartsCount: consecutiveCount.chartsCount,
      tablesCount: consecutiveCount.tablesCount,
    });
  }

  // Cut-In to Cut-Out
  const cutinoutCount = countSectionItems('cutinout');
  if (cutinoutCount.chartsCount > 0 || cutinoutCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'cutinout',
      label: 'Cut-In à Cut-Out',
      icon: <Activity className="w-4 h-4" />,
      chartsCount: cutinoutCount.chartsCount,
      tablesCount: cutinoutCount.tablesCount,
    });
  }

  // Nominal Power
  const nominalCount = countSectionItems('nominal');
  if (nominalCount.chartsCount > 0 || nominalCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'nominal',
      label: 'Puissance nominale',
      icon: <Zap className="w-4 h-4" />,
      chartsCount: nominalCount.chartsCount,
      tablesCount: nominalCount.tablesCount,
    });
  }

  // Local Restarts
  const restartsCount = countSectionItems('restarts');
  if (restartsCount.chartsCount > 0 || restartsCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'restarts',
      label: 'Redémarrages locaux',
      icon: <RotateCcw className="w-4 h-4" />,
      chartsCount: restartsCount.chartsCount,
      tablesCount: restartsCount.tablesCount,
    });
  }

  // Availability
  const availabilityCount = countSectionItems('availability');
  if (availabilityCount.chartsCount > 0 || availabilityCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'availability',
      label: 'Disponibilité',
      icon: <CheckCircle className="w-4 h-4" />,
      chartsCount: availabilityCount.chartsCount,
      tablesCount: availabilityCount.tablesCount,
    });
  }

  // Wind Rose
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

  // Wind Histogram
  const windHistogramCount = countSectionItems('wind-histogram');
  if (windHistogramCount.chartsCount > 0 || windHistogramCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'wind-histogram',
      label: 'Distribution vent',
      icon: <BarChart3 className="w-4 h-4" />,
      chartsCount: windHistogramCount.chartsCount,
      tablesCount: windHistogramCount.tablesCount,
    });
  }

  // Power Curve
  const powerCurveCount = countSectionItems('power-curve');
  if (powerCurveCount.chartsCount > 0 || powerCurveCount.tablesCount > 0) {
    sidebarSections.push({
      id: 'power-curve',
      label: 'Courbe de puissance',
      icon: <Zap className="w-4 h-4" />,
      chartsCount: powerCurveCount.chartsCount,
      tablesCount: powerCurveCount.tablesCount,
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
    'validation': (
      <CategoryCard title="Résumé de validation" icon={CheckCircle} defaultOpen={true}>
        <ValidationSummary result={result} />
      </CategoryCard>
    ),
    'summary': renderSection('Tableau récapitulatif', Info),
    'consecutive': renderSection('120 heures consécutives', Clock),
    'cutinout': renderSection('Test Cut-In à Cut-Out', Activity),
    'nominal': renderSection('Puissance nominale', Zap),
    'restarts': renderSection('Redémarrages locaux', RotateCcw),
    'availability': renderSection('Disponibilité', CheckCircle),
    'wind-rose': renderSection('Rose des vents', Wind),
    'wind-histogram': renderSection('Distribution de la vitesse du vent', BarChart3),
    'power-curve': renderSection('Courbe de puissance', Zap),
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
          <CategoryCard title="Téléchargement" icon={CheckCircle} defaultOpen={true} collapsible={false}>
            <DownloadButton reportPath={result.report_path} />
          </CategoryCard>
        </div>
      </div>
    </div>
  );
}
