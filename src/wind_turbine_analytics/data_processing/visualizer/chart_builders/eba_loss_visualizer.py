from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
import plotly.graph_objects as go
import pandas as pd
from src.logger_config import get_logger
import seaborn as sns

logger = get_logger(__name__)


class EbaLossVisualizer(BaseVisualizer):
    """
    Visualiseur pour les pertes d'énergie mensuelles (EBA Manufacturer).

    Génère un histogramme avec:
    - Axe X: Périodes mensuelles
    - Axe Y: Pourcentage de perte d'énergie (0-100%)
    - Barres par turbine avec dégradé de couleur (bleu → rouge)
    - Support PNG + JSON pour dashboard web futur
    """

    def __init__(self, output_dir=None):
        super().__init__(chart_name="eba_loss_chart", use_plotly=True, output_dir=output_dir)

    def _create_figure(self, result: AnalysisResult) -> go.Figure:
        """
        Crée la figure Plotly avec histogramme des pertes d'énergie.

        Args:
            result: Résultat de EbaManufacturerAnalyzer contenant:
                - monthly_performance: list[dict] avec 'month' et 'performance'
                - Loss_energy_monthly est calculé à partir de performance

        Returns:
            Figure Plotly avec histogramme
        """

        if not result.detailed_results:
            logger.warning(
                "Aucune donnée détaillée pour générer le graphique des pertes EBA"
            )
            return self._create_empty_figure()

        turbine_ids = list(result.detailed_results.keys())

        # Créer la figure
        fig = go.Figure()

        # Collecter toutes les données pour normaliser les couleurs
        all_loss_percentages = []
        monthly_data_by_turbine = {}

        # Première passe : collecter toutes les pertes pour la normalisation des couleurs
        for turbine_id in turbine_ids:
            turbine_data = result.detailed_results[turbine_id]

            if "error" in turbine_data:
                logger.warning(
                    f"Erreur dans les données de {turbine_id}: {turbine_data.get('error')}"
                )
                continue

            monthly_data = turbine_data.get("monthly_performance", [])

            if not monthly_data:
                logger.warning(f"Pas de données mensuelles pour {turbine_id}")
                continue

            # Convertir en DataFrame
            df_monthly = pd.DataFrame(monthly_data)

            if (
                "month" not in df_monthly.columns
                or "performance" not in df_monthly.columns
            ):
                logger.warning(f"Colonnes manquantes pour {turbine_id}")
                continue

            # Calculer les pertes en pourcentage (100 - performance)
            df_monthly["loss_percent"] = 100.0 - df_monthly["performance"]
            df_monthly["month_str"] = df_monthly["month"].astype(str)

            monthly_data_by_turbine[turbine_id] = df_monthly
            all_loss_percentages.extend(df_monthly["loss_percent"].tolist())

        if not all_loss_percentages:
            logger.warning("Aucune donnée de perte disponible")
            return self._create_empty_figure()

        # Log des statistiques sur les pertes
        min_loss = min(all_loss_percentages)
        max_loss = max(all_loss_percentages)
        avg_loss = sum(all_loss_percentages) / len(all_loss_percentages)

        logger.debug(
            f"Statistiques des pertes d'énergie: "
            f"min={min_loss:.2f}%, max={max_loss:.2f}%, moyenne={avg_loss:.2f}%"
        )

        # Créer une palette de couleurs du bleu au rouge en fonction des pertes
        # Utiliser seaborn pour générer un dégradé de couleurs

        # Générer une palette de couleurs du bleu au rouge
        # On utilise la palette "coolwarm" de seaborn (bleu → rouge)
        n_colors = 100
        color_palette = sns.color_palette("coolwarm", n_colors=n_colors).as_hex()

        def get_color(loss_value: float) -> str:
            """Retourne la couleur correspondant au pourcentage de perte."""
            if max_loss == min_loss:
                # Si toutes les pertes sont identiques, retourner une couleur centrale
                return color_palette[n_colors // 2]

            # Normaliser entre 0 et 1
            normalized = (loss_value - min_loss) / (max_loss - min_loss)
            # Mapper sur l'index de la palette
            color_idx = int(normalized * (n_colors - 1))
            return color_palette[color_idx]

        # Deuxième passe : créer les barres pour chaque turbine
        all_months = sorted(
            set(
                month
                for df in monthly_data_by_turbine.values()
                for month in df["month_str"]
            )
        )

        for turbine_id in turbine_ids:
            df_monthly = monthly_data_by_turbine.get(turbine_id)

            if df_monthly is None:
                continue

            # Préparer les données pour toutes les périodes
            loss_data = []
            colors = []

            for month in all_months:
                month_data = df_monthly[df_monthly["month_str"] == month]
                if not month_data.empty:
                    loss_value = month_data["loss_percent"].iloc[0]
                    loss_data.append(loss_value)
                    colors.append(get_color(loss_value))
                else:
                    loss_data.append(None)  # None au lieu de 0 pour ne pas afficher
                    colors.append(color_palette[0])

            # Ajouter la trace pour cette turbine
            # En mode "group", Plotly gère automatiquement le positionnement
            fig.add_trace(
                go.Bar(
                    x=all_months,
                    y=loss_data,
                    name=turbine_id,
                    marker=dict(color=colors, line=dict(color="white", width=1)),
                    text=[f"{v:.2f}%" if v is not None else "" for v in loss_data],
                    textposition="outside",
                    hovertemplate=(
                        f"<b>{turbine_id}</b><br>"
                        "Period: %{x}<br>"
                        "Loss: %{y:.2f}%<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Mise en page
        fig.update_layout(
            title={
                "text": "Monthly Energy Loss",
                "font": {"size": 16},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis=dict(
                title="Period (Month)",
                showgrid=True,
                gridcolor="lightgray",
                tickangle=-45,
            ),
            yaxis=dict(
                title="Energy Loss (%)",
                showgrid=True,
                gridcolor="lightgray",
                range=[0, max(max(all_loss_percentages) * 1.2, 1)],  # Min 1%, ou max+20%
                ticksuffix="%",
            ),
            height=600,
            width=1200,
            template="plotly_white",
            barmode="group",  # Barres groupées par période
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
            ),
            hovermode="x unified",
        )

        return fig

    def _create_empty_figure(self) -> go.Figure:
        """Crée une figure vide en cas de données manquantes."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for EBA Loss analysis",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="red"),
        )
        fig.update_layout(
            title="Energy Loss Analysis (EBA Manufacturer)",
            height=400,
            width=600,
            template="plotly_white",
        )
        return fig
