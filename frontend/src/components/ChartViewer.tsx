import { useEffect, useRef, useState } from "react";
import type { ChartData } from "../types/analysis";

// @ts-ignore - Plotly types
import Plotly from "plotly.js-dist-min";

interface ChartViewerProps {
  charts: ChartData[];
}

export const ChartViewer = ({ charts }: ChartViewerProps) => {
  console.log("📊 ChartViewer rendering with", charts.length, "charts");

  if (charts.length === 0) {
    console.log("⚠️ No charts to display");
    return null;
  }

  return (
    <div className="space-y-6">
      {charts.map((chart, idx) => (
        <ChartContainer key={`${chart.name}-${idx}`} chart={chart} />
      ))}
    </div>
  );
};

interface ChartContainerProps {
  chart: ChartData;
}

const ChartContainer = ({ chart }: ChartContainerProps) => {
  const plotRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isRendered, setIsRendered] = useState(false);

  useEffect(() => {
    if (plotRef.current && containerRef.current && chart.plotly_json) {
      try {
        const layout = chart.plotly_json.layout || {};

        // Calculer le padding en fonction de la taille d'écran
        const screenWidth = window.innerWidth;
        const padding = screenWidth < 640 ? 16 : screenWidth < 1024 ? 24 : 32;
        const containerWidth = containerRef.current.offsetWidth - padding;

        // Calculer la hauteur en fonction du type de graphique et de la taille d'écran
        let baseHeight = screenWidth < 640 ? 400 : screenWidth < 1024 ? 500 : 600;
        let height = layout.height || baseHeight;

        // Détecter s'il y a plusieurs subplots
        const hasMultipleSubplots = layout.grid || (layout.xaxis && layout.xaxis2);

        // Si c'est un graphique avec plusieurs subplots (grille), augmenter la hauteur
        if (hasMultipleSubplots) {
          const minHeightForSubplots = screenWidth < 640 ? 600 : screenWidth < 1024 ? 700 : 800;
          height = Math.max(height, minHeightForSubplots);
        }

        // Ajuster les marges selon le type de graphique et la taille d'écran
        const marginScale = screenWidth < 640 ? 0.7 : screenWidth < 1024 ? 0.85 : 1;
        let margins = layout.margin || {
          l: Math.round(60 * marginScale),
          r: Math.round(40 * marginScale),
          t: Math.round(60 * marginScale),
          b: Math.round(80 * marginScale),
        };

        // Pour les graphiques avec subplots côte à côte, augmenter l'espacement en bas
        if (hasMultipleSubplots) {
          margins = {
            l: margins.l || Math.round(60 * marginScale),
            r: margins.r || Math.round(40 * marginScale),
            t: margins.t || Math.round(80 * marginScale),
            b: Math.max(margins.b || Math.round(100 * marginScale), Math.round(100 * marginScale)),
          };
        }

        Plotly.newPlot(
          plotRef.current,
          chart.plotly_json.data || [],
          {
            ...layout,
            autosize: false, // Désactiver autosize pour contrôler manuellement
            width: containerWidth, // Forcer la largeur
            height: height,
            margin: margins,
          },
          {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
          }
        );

        setIsRendered(true);
        console.log("✅ Chart rendered:", chart.name, "width:", containerWidth);

        // Force un resize après un court délai pour s'assurer que tout est bien affiché
        setTimeout(() => {
          if (plotRef.current && containerRef.current) {
            const screenWidth = window.innerWidth;
            const padding = screenWidth < 640 ? 16 : screenWidth < 1024 ? 24 : 32;
            const newWidth = containerRef.current.offsetWidth - padding;
            Plotly.relayout(plotRef.current, { width: newWidth });
          }
        }, 100);
      } catch (error) {
        console.error("❌ Failed to render chart:", chart.name, error);
      }
    }

    // Cleanup
    return () => {
      if (plotRef.current) {
        Plotly.purge(plotRef.current);
      }
    };
  }, [chart]);

  // Re-render sur resize de la fenêtre
  useEffect(() => {
    if (!isRendered || !plotRef.current || !containerRef.current) return;

    const handleResize = () => {
      if (plotRef.current && containerRef.current) {
        const screenWidth = window.innerWidth;
        const padding = screenWidth < 640 ? 16 : screenWidth < 1024 ? 24 : 32;
        const newWidth = containerRef.current.offsetWidth - padding;
        Plotly.relayout(plotRef.current, { width: newWidth });
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [isRendered]);

  return (
    <div ref={containerRef} className="bg-white p-2 sm:p-3 lg:p-4 rounded-lg shadow-md w-full">
      <h3 className="text-sm sm:text-base lg:text-lg font-semibold mb-2 sm:mb-3 text-gray-700">{chart.name}</h3>
      <div ref={plotRef} className="w-full min-h-[400px] sm:min-h-[500px] lg:min-h-[600px] overflow-hidden" />
    </div>
  );
};
