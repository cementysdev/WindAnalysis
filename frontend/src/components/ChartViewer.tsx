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
        const containerWidth = containerRef.current.offsetWidth - 32; // Soustraire le padding (p-4 = 16px de chaque côté)

        // Calculer la hauteur en fonction du type de graphique
        let height = layout.height || 600;

        // Détecter s'il y a plusieurs subplots
        const hasMultipleSubplots = layout.grid || (layout.xaxis && layout.xaxis2);

        // Si c'est un graphique avec plusieurs subplots (grille), augmenter la hauteur
        if (hasMultipleSubplots) {
          height = Math.max(height, 800);
        }

        // Ajuster les marges selon le type de graphique
        let margins = layout.margin || { l: 60, r: 40, t: 60, b: 80 };

        // Pour les graphiques avec subplots côte à côte, augmenter l'espacement en bas
        if (hasMultipleSubplots) {
          margins = {
            l: margins.l || 60,
            r: margins.r || 40,
            t: margins.t || 80,
            b: Math.max(margins.b || 100, 100), // Au moins 100px en bas pour les labels
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
            const newWidth = containerRef.current.offsetWidth - 32;
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
        const newWidth = containerRef.current.offsetWidth - 32;
        Plotly.relayout(plotRef.current, { width: newWidth });
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [isRendered]);

  return (
    <div ref={containerRef} className="bg-white p-4 rounded-lg shadow-md w-full">
      <h3 className="text-lg font-semibold mb-3 text-gray-700">{chart.name}</h3>
      <div ref={plotRef} className="w-full min-h-[600px] overflow-hidden" />
    </div>
  );
};
