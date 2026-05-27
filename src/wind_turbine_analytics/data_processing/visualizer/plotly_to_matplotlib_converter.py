"""
Convertisseur Plotly → Matplotlib pour génération PNG sans Kaleido.
Lit une figure Plotly et la recrée en Matplotlib.
"""

import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.gridspec as gridspec
import numpy as np
from typing import Optional, Dict, Tuple
from src.logger_config import get_logger

logger = get_logger(__name__)


class PlotlyToMatplotlibConverter:
    """
    Convertit une figure Plotly en figure Matplotlib.
    Supporte les types de graphiques courants dans Wind Analytics.
    """

    @staticmethod
    def _clean_html_tags(text: str) -> str:
        """
        Nettoie les balises HTML d'un texte.

        Args:
            text: Texte potentiellement avec balises HTML

        Returns:
            Texte sans balises HTML
        """
        if not text:
            return text

        # Supprimer les balises HTML courantes
        text = text.replace('<b>', '').replace('</b>', '')
        text = text.replace('<i>', '').replace('</i>', '')
        text = text.replace('<br>', ' ').replace('<br/>', ' ')
        text = text.replace('<sub>', '').replace('</sub>', '')
        text = text.replace('<sup>', '').replace('</sup>', '')
        text = text.replace('<span style=\'font-size:12px; color:gray;\'>', '')
        text = text.replace('</span>', '')

        return text.strip()

    @staticmethod
    def convert(plotly_fig: go.Figure) -> matplotlib.figure.Figure:
        """
        Convertit une figure Plotly en Matplotlib.
        Gère automatiquement les subplots et figures simples.

        Args:
            plotly_fig: Figure Plotly source

        Returns:
            Figure Matplotlib équivalente

        Raises:
            NotImplementedError: Si le type de graphique n'est pas supporté
        """
        # Extraire les dimensions du layout
        layout = plotly_fig.layout

        # Détecter présence de subplots
        if PlotlyToMatplotlibConverter._has_subplots(plotly_fig):
            logger.debug("Subplots détectés, conversion en grille Matplotlib")

            # Calculer grille (UNE SEULE FOIS)
            rows, cols, subplot_types = (
                PlotlyToMatplotlibConverter._detect_subplot_grid(plotly_fig)
            )
            logger.debug(f"Grille détectée: {rows} rows × {cols} cols")

            # Calculer figsize APRÈS rows/cols
            figsize = (7 * cols, 5 * rows)

            fig, axes = PlotlyToMatplotlibConverter._create_matplotlib_grid(
                rows, cols, subplot_types, figsize
            )

            # Extraire et appliquer les titres des subplots de Plotly
            subplot_titles = PlotlyToMatplotlibConverter._extract_subplot_titles(plotly_fig)

            # Router chaque trace vers son subplot
            for trace in plotly_fig.data:
                row, col, _ = PlotlyToMatplotlibConverter._get_trace_position(
                    trace, cols
                )

                # Gérer le cas d'un seul subplot ou grille
                if rows == 1 and cols == 1:
                    ax = axes[0, 0]
                else:
                    ax = axes[row, col]

                # Ne traiter que si l'axe existe (pas None)
                if ax is not None:
                    PlotlyToMatplotlibConverter._add_trace(ax, trace)

                    # Appliquer le titre du subplot si disponible
                    subplot_key = (row, col)
                    if subplot_key in subplot_titles:
                        # Nettoyer le titre HTML
                        title = PlotlyToMatplotlibConverter._clean_html_tags(subplot_titles[subplot_key])
                        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)

            # Appliquer layout global (titre principal)
            PlotlyToMatplotlibConverter._apply_layout(
                fig, None, layout, is_subplot=True, axes=axes
            )
        else:
            # Chemin simple
            # Détecter Data Availability (beaucoup de barres horizontales)
            n_horizontal_bars = sum(
                1 for trace in plotly_fig.data
                if getattr(trace, 'orientation', 'v') == 'h'
            )

            # Utiliser les dimensions du layout Plotly si disponibles
            width = layout.width if layout.width else 1200
            height = layout.height if layout.height else 800

            # Data Availability: Respecter la hauteur Plotly
            if n_horizontal_bars > 20 and height > 800:
                # Plotly a déjà calculé la hauteur optimale
                figsize = (width / 100, height / 100)
            elif n_horizontal_bars > 20:
                # Fallback: hauteur dynamique basée sur nombre de catégories Y
                unique_y = set()
                for trace in plotly_fig.data:
                    if hasattr(trace, 'y') and trace.y is not None:
                        if hasattr(trace.y, '__iter__'):
                            unique_y.update(trace.y)
                        else:
                            unique_y.add(trace.y)
                n_categories = len(unique_y)
                height = max(600, n_categories * 50)  # 50px par ligne (barres épaisses)
                figsize = (15, height / 100)
            else:
                # Standard
                figsize = (width / 100, height / 100)

            fig, ax = plt.subplots(figsize=figsize)

            # Tracker pour éviter les doublons de légende
            legend_groups_shown = set()

            for trace in plotly_fig.data:
                PlotlyToMatplotlibConverter._add_trace(ax, trace, legend_groups_shown)

            PlotlyToMatplotlibConverter._apply_layout(
                fig, ax, layout, is_subplot=False
            )

        return fig

    @staticmethod
    def _extract_subplot_titles(plotly_fig: go.Figure) -> Dict[Tuple[int, int], str]:
        """
        Extrait les titres des subplots depuis les annotations Plotly.

        Plotly stocke les titres dans layout.annotations avec x, y et text.

        Returns:
            Dict mapping (row, col) → title text
        """
        titles = {}
        layout = plotly_fig.layout

        if not hasattr(layout, 'annotations') or not layout.annotations:
            return titles

        # Détecter le nombre de colonnes (pour mapper position → row/col)
        max_subplot_num = 1
        for attr in dir(layout):
            if attr.startswith(('xaxis', 'yaxis', 'polar')) and attr[5:].isdigit():
                try:
                    num = int(attr[5:])
                    max_subplot_num = max(max_subplot_num, num)
                except ValueError:
                    pass

        n_subplots = max_subplot_num
        cols = min(n_subplots, 2)

        # Les annotations avec xref="paper" et yref="paper" sont les titres de subplots
        subplot_annotations = [
            ann for ann in layout.annotations
            if hasattr(ann, 'xref') and ann.xref == 'paper' and
               hasattr(ann, 'yref') and ann.yref == 'paper' and
               hasattr(ann, 'text') and ann.text
        ]

        # Mapper chaque annotation à une position (row, col) basée sur x, y
        for idx, ann in enumerate(subplot_annotations):
            # Heuristique: les annotations sont ordonnées comme les subplots
            subplot_num = idx + 1
            row = (subplot_num - 1) // cols
            col = (subplot_num - 1) % cols
            titles[(row, col)] = ann.text

        return titles

    @staticmethod
    def _has_subplots(plotly_fig: go.Figure) -> bool:
        """Détecte si la figure Plotly contient des subplots."""
        layout = plotly_fig.layout

        # Vérifier présence de xaxis2, yaxis2, polar2, etc.
        has_cartesian_subplots = any([
            hasattr(layout, f'xaxis{i}') or hasattr(layout, f'yaxis{i}')
            for i in range(2, 20)  # Supporter jusqu'à 20 subplots
        ])

        has_polar_subplots = any([
            hasattr(layout, f'polar{i}')
            for i in range(2, 20)
        ])

        return has_cartesian_subplots or has_polar_subplots

    @staticmethod
    def _get_trace_position(trace, cols: int) -> Tuple[int, int, str]:
        """
        Extrait la position (row, col, type) d'un trace.

        Returns:
            (row, col, plot_type) où plot_type est 'cartesian' ou 'polar'
        """
        # Traces polaires
        if hasattr(trace, 'subplot') and trace.subplot:
            subplot_name = trace.subplot  # "polar", "polar2", etc.
            if 'polar' in subplot_name:
                plot_type = 'polar'
                # Extraire numéro : "polar" → 1, "polar2" → 2
                if subplot_name == 'polar':
                    subplot_num = 1
                else:
                    # "polar2" → 2
                    subplot_num = int(subplot_name.replace('polar', ''))

                # Convertir en (row, col) row-major
                row = (subplot_num - 1) // cols
                col = (subplot_num - 1) % cols
                return (row, col, plot_type)

        # Traces cartésiennes
        xaxis = getattr(trace, 'xaxis', 'x')
        yaxis = getattr(trace, 'yaxis', 'y')

        # Extraire numéros : "x" → 1, "x2" → 2, etc.
        if xaxis == 'x':
            x_num = 1
        else:
            x_num = int(xaxis[1:])

        # Plotly utilise xaxis/yaxis de manière synchronisée
        subplot_num = x_num

        # Convertir en (row, col) row-major (0-indexed)
        row = (subplot_num - 1) // cols
        col = (subplot_num - 1) % cols

        return (row, col, 'cartesian')

    @staticmethod
    def _detect_subplot_grid(plotly_fig: go.Figure) -> Tuple[int, int, Dict]:
        """
        Détecte la disposition des subplots (rows, cols, types).

        Returns:
            (rows, cols, subplot_types) où subplot_types est un dict {(row,col): 'cartesian'/'polar'}
        """
        layout = plotly_fig.layout

        # Compter le nombre total de subplots
        max_subplot_num = 1

        # Vérifier axes cartésiens
        for attr in dir(layout):
            if attr.startswith('xaxis') and attr != 'xaxis':
                try:
                    num = int(attr[5:])  # "xaxis2" → 2
                    max_subplot_num = max(max_subplot_num, num)
                except ValueError:
                    pass

        # Vérifier axes polaires
        for attr in dir(layout):
            if attr.startswith('polar') and attr != 'polar':
                try:
                    num = int(attr[5:])  # "polar2" → 2
                    max_subplot_num = max(max_subplot_num, num)
                except ValueError:
                    pass

        n_subplots = max_subplot_num

        # Inférer rows/cols (heuristique: max 2 colonnes pour lisibilité)
        cols = min(n_subplots, 2)
        rows = (n_subplots + cols - 1) // cols

        # Mapper chaque trace à sa position pour déterminer le type
        subplot_types = {}

        for trace in plotly_fig.data:
            row, col, plot_type = PlotlyToMatplotlibConverter._get_trace_position(trace, cols)
            subplot_types[(row, col)] = plot_type

        return rows, cols, subplot_types

    @staticmethod
    def _create_matplotlib_grid(rows: int, cols: int, subplot_types: Dict, figsize: Tuple) -> Tuple:
        """
        Crée une grille Matplotlib avec support polar.

        Args:
            rows, cols: Dimensions grille
            subplot_types: Dict {(row,col): 'cartesian'/'polar'}
            figsize: Taille figure

        Returns:
            (fig, axes) où axes est un array 2D d'axes
        """
        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(rows, cols, figure=fig)

        axes = np.empty((rows, cols), dtype=object)

        for row in range(rows):
            for col in range(cols):
                # Ne créer un subplot QUE si des traces y sont assignées
                if (row, col) in subplot_types:
                    plot_type = subplot_types[(row, col)]

                    if plot_type == 'polar':
                        ax = fig.add_subplot(gs[row, col], projection='polar')
                    else:
                        ax = fig.add_subplot(gs[row, col])

                    axes[row, col] = ax
                else:
                    # Masquer les positions vides
                    axes[row, col] = None

        return fig, axes

    @staticmethod
    def _add_trace(ax, trace, legend_groups_shown=None):
        """Ajoute une trace Plotly à l'axe Matplotlib."""
        trace_type = trace.type

        if trace_type == "bar":
            PlotlyToMatplotlibConverter._add_bar(ax, trace, legend_groups_shown)
        elif trace_type in ["scatter", "scattergl"]:
            PlotlyToMatplotlibConverter._add_scatter(ax, trace)
        elif trace_type == "histogram":
            PlotlyToMatplotlibConverter._add_histogram(ax, trace)
        elif trace_type == "barpolar":
            PlotlyToMatplotlibConverter._add_barpolar(ax, trace)
        elif trace_type == "treemap":
            PlotlyToMatplotlibConverter._add_treemap(ax, trace)
        else:
            logger.warning(
                f"Type de trace '{trace_type}' non implémenté, rendu basique"
            )
            # Rendu basique par défaut
            if hasattr(trace, 'x') and hasattr(trace, 'y'):
                x_data = trace.x if trace.x is not None else []
                y_data = trace.y if trace.y is not None else []
                if len(x_data) > 0 and len(y_data) > 0:
                    ax.plot(x_data, y_data, label=trace.name if trace.name else None)

    @staticmethod
    def _add_bar(ax, trace, legend_groups_shown=None):
        """Ajoute un bar chart."""
        # Utiliser is None au lieu de truthiness pour éviter erreur NumPy
        x = trace.x if trace.x is not None else []
        y = trace.y if trace.y is not None else []

        # Vérifier que les données ne sont pas vides
        if len(x) == 0 or len(y) == 0:
            return

        # Gérer legendgroup pour éviter les doublons
        legendgroup = getattr(trace, 'legendgroup', None)
        show_legend = True
        if legend_groups_shown is not None and legendgroup:
            if legendgroup in legend_groups_shown:
                show_legend = False
            else:
                legend_groups_shown.add(legendgroup)

        # Déterminer le label de la légende
        label = trace.name if (trace.name and show_legend) else None

        # Extraire couleurs si disponibles
        colors = None
        if trace.marker and hasattr(trace.marker, 'color'):
            colors = trace.marker.color
            # Si c'est une couleur unique (string), pas une liste
            if isinstance(colors, str):
                colors = [colors] * len(x)
            # Si colors est une liste de valeurs numériques avec colorscale
            elif hasattr(trace.marker, 'colorscale') and trace.marker.colorscale:
                # Utiliser matplotlib colormap au lieu de colorscale Plotly
                import matplotlib.cm as cm
                import numpy as np

                # Mapper colorscale Plotly vers matplotlib
                colorscale_map = {
                    'YlOrRd': 'YlOrRd',
                    'Reds': 'Reds',
                    'Blues': 'Blues',
                    'Greens': 'Greens',
                }
                cmap_name = colorscale_map.get(trace.marker.colorscale, 'viridis')

                # Normaliser les valeurs
                if len(colors) > 0:
                    colors_array = np.array(colors)
                    norm = plt.Normalize(vmin=colors_array.min(), vmax=colors_array.max())
                    cmap = cm.get_cmap(cmap_name)
                    colors = [cmap(norm(val)) for val in colors]

        # Détecter orientation (Timeline utilise orientation="h")
        orientation = getattr(trace, 'orientation', 'v')

        # Détecter base (Timeline utilise base=start_time)
        base = getattr(trace, 'base', None)

        if orientation == 'h':
            # Barres horizontales
            if base is not None:
                # Détecter Timeline (base=datetime)
                import matplotlib.dates as mdates
                from datetime import datetime
                import pandas as pd

                # Vérifier si base contient des datetime
                is_timeline = False

                # Cas 1: base est un seul datetime (scalaire)
                if isinstance(base, (datetime, pd.Timestamp)):
                    is_timeline = True
                    base = [base]  # Convertir en liste pour traitement uniforme
                # Cas 2: base est une string ISO format (ex: "2024-04-01T00:00:00")
                elif isinstance(base, str):
                    try:
                        # Essayer de parser comme datetime
                        parsed_date = pd.to_datetime(base)
                        is_timeline = True
                        base = [parsed_date]
                    except:
                        pass
                # Cas 3: base est une liste/array de datetime ou strings
                elif hasattr(base, '__iter__') and len(base) > 0:
                    first_elem = base[0]
                    if isinstance(first_elem, (datetime, pd.Timestamp)):
                        is_timeline = True
                    elif isinstance(first_elem, str):
                        try:
                            # Essayer de parser toute la liste
                            base = pd.to_datetime(base)
                            is_timeline = True
                        except:
                            pass

                if is_timeline:
                    # TIMELINE: Conversion datetime + millisecondes
                    from src.logger_config import get_logger
                    logger = get_logger(__name__)
                    logger.debug(f"✅ Timeline détecté - base={base[:2] if len(base) > 2 else base}, x={x[:2] if len(x) > 2 else x}, y={y}")

                    # Convertir base (datetime) → nombres matplotlib
                    base_numeric = mdates.date2num(base)

                    # Convertir x (millisecondes) → jours
                    # 1 jour = 86400000 ms
                    x_days = [ms / 86400000.0 for ms in x]

                    # Tracer avec données converties
                    ax.barh(
                        y,
                        x_days,
                        left=base_numeric,
                        label=label,
                        color=colors if colors else None,
                        alpha=0.8,
                        edgecolor='white',
                        linewidth=0.5
                    )

                    # Configurer axe X comme temporel
                    ax.xaxis.set_major_formatter(
                        mdates.DateFormatter('%d/%m\n%H:%M')
                    )
                    ax.xaxis.set_major_locator(mdates.AutoDateLocator())

                    # Rotation labels
                    import matplotlib.pyplot as plt
                    plt.setp(
                        ax.xaxis.get_majorticklabels(),
                        rotation=0,
                        ha='center'
                    )

                    return  # Sortir après traitement timeline

                # Cas standard (base numérique)
                ax.barh(
                    y,
                    x,
                    left=base,
                    label=label,
                    color=colors if colors else None,
                    alpha=0.8
                )
            else:
                ax.barh(
                    y,
                    x,
                    label=label,
                    color=colors if colors else None,
                    alpha=0.8
                )
        else:
            # Barres verticales (standard)
            ax.bar(
                x,
                y,
                label=label,
                color=colors if colors else None,
                alpha=0.8
            )

    @staticmethod
    def _add_scatter(ax, trace):
        """Ajoute un scatter plot ou line."""
        # Utiliser is None au lieu de truthiness pour éviter erreur NumPy
        x = trace.x if trace.x is not None else []
        y = trace.y if trace.y is not None else []

        # Vérifier que les données ne sont pas vides
        if len(x) == 0 or len(y) == 0:
            return

        # Détecter si x contient des dates (format YYYY-MM-DD)
        import pandas as pd
        from datetime import datetime
        is_datetime_axis = False
        if len(x) > 0:
            first_x = x[0]
            # Vérifier si c'est une date string (YYYY-MM-DD) ou datetime
            if isinstance(first_x, str) and len(first_x) == 10 and first_x[4] == '-':
                try:
                    x = pd.to_datetime(x)
                    is_datetime_axis = True
                except:
                    pass
            elif isinstance(first_x, (datetime, pd.Timestamp)):
                is_datetime_axis = True

        mode = trace.mode if hasattr(trace, 'mode') else 'lines+markers'

        # Extraire couleur
        color = None
        if trace.line and hasattr(trace.line, 'color'):
            color = trace.line.color
        elif trace.marker and hasattr(trace.marker, 'color'):
            marker_color = trace.marker.color
            if isinstance(marker_color, str):
                color = marker_color

        # Déterminer le style de ligne
        linestyle = '-'
        if trace.line and hasattr(trace.line, 'dash'):
            dash_type = trace.line.dash
            if dash_type == 'dash':
                linestyle = '--'
            elif dash_type == 'dot':
                linestyle = ':'

        # Taille des marqueurs et opacité
        marker_size = 6
        alpha = 0.8  # Default opacity
        if trace.marker:
            if hasattr(trace.marker, 'size') and trace.marker.size:
                marker_size = trace.marker.size
            if hasattr(trace.marker, 'opacity') and trace.marker.opacity:
                alpha = trace.marker.opacity

        # Tracer selon le mode
        if 'lines' in mode and 'markers' in mode:
            ax.plot(
                x, y,
                label=trace.name if trace.name else None,
                color=color,
                linestyle=linestyle,
                marker='o',
                markersize=marker_size,
                linewidth=2,
                alpha=alpha
            )
        elif 'lines' in mode:
            ax.plot(
                x, y,
                label=trace.name if trace.name else None,
                color=color,
                linestyle=linestyle,
                linewidth=2,
                alpha=alpha
            )
        elif 'markers' in mode:
            ax.scatter(
                x, y,
                label=trace.name if trace.name else None,
                c=color if isinstance(color, str) else None,
                s=marker_size * 5,  # Matplotlib uses larger values
                alpha=alpha
            )

        # Configurer axe X pour dates si détecté
        if is_datetime_axis:
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center', fontsize=10)

    @staticmethod
    def _add_histogram(ax, trace):
        """Ajoute un histogramme."""
        # Plotly histogram peut avoir x ou y
        data = None
        if hasattr(trace, 'x') and trace.x is not None:
            data = trace.x
        elif hasattr(trace, 'y') and trace.y is not None:
            data = trace.y

        if data is None or len(data) == 0:
            return

        # Extraire couleur
        color = None
        if trace.marker and hasattr(trace.marker, 'color'):
            marker_color = trace.marker.color
            if isinstance(marker_color, str):
                color = marker_color

        # Nombre de bins (par défaut Plotly utilise autobinning)
        nbins = 30
        if hasattr(trace, 'nbinsx') and trace.nbinsx:
            nbins = trace.nbinsx
        elif hasattr(trace, 'nbinsy') and trace.nbinsy:
            nbins = trace.nbinsy

        ax.hist(
            data,
            bins=nbins,
            label=trace.name if trace.name else None,
            color=color,
            alpha=0.7,
            edgecolor='white',
            linewidth=0.5
        )

    @staticmethod
    def _add_barpolar(ax, trace):
        """Convertit un Barpolar Plotly en bar chart Matplotlib polaire."""
        # Données
        r = trace.r if hasattr(trace, 'r') and trace.r is not None else []
        theta = trace.theta if hasattr(trace, 'theta') and trace.theta is not None else []
        base = trace.base if hasattr(trace, 'base') and trace.base is not None else None

        if len(r) == 0 or len(theta) == 0:
            logger.debug(f"Trace barpolar '{trace.name}' vide, ignorée")
            return

        # Convertir en arrays NumPy pour calculs
        r = np.array(r)
        theta = np.array(theta)

        # Base (pour stacking)
        if base is None:
            base = np.zeros(len(r))
        else:
            base = np.array(base)

        # Convertir theta en radians (Plotly utilise degrés)
        theta_rad = np.deg2rad(theta)

        # Largeur des barres (360° / nombre de secteurs)
        width = 2 * np.pi / len(theta)

        # Couleur
        color = None
        if trace.marker and hasattr(trace.marker, 'color'):
            color = trace.marker.color
            # Si c'est une liste, prendre le premier élément pour uniformité
            if isinstance(color, list) and len(color) > 0:
                color = color[0]

        # Tracer barres polaires
        ax.bar(
            theta_rad,
            r,
            width=width,
            bottom=base,
            color=color,
            alpha=0.8,
            edgecolor='white',
            linewidth=0.5,
            label=trace.name if trace.name else None
        )

        # Configuration axes polaires (équivalence exacte Plotly→Matplotlib)
        # Direction clockwise (sens horaire)
        ax.set_theta_direction(-1)

        # Nord en haut (rotation 90°)
        ax.set_theta_offset(np.pi / 2)

        # Labels des directions (16 secteurs Wind Rose)
        directions_deg = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5,
                          180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5]
        dir_labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

        ax.set_xticks(np.deg2rad(directions_deg))
        ax.set_xticklabels(dir_labels, fontsize=10)

        # Format radial axis (pourcentage pour Wind Rose)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))

        # Grille
        ax.grid(True, color='gray', alpha=0.3, linewidth=0.5)

    @staticmethod
    def _add_treemap(ax, trace):
        """
        Convertit un Treemap Plotly en barres horizontales Matplotlib.
        Fallback car Matplotlib ne supporte pas nativement les treemaps.
        """
        # Extraire données hiérarchiques
        labels = trace.labels if hasattr(trace, 'labels') else []
        parents = trace.parents if hasattr(trace, 'parents') else []
        values = trace.values if hasattr(trace, 'values') else []

        if not labels or not values:
            logger.warning("Treemap vide, données manquantes")
            return

        # Construire hiérarchie (niveau 0 = root)
        root_items = [
            (l, v) for l, p, v in zip(labels, parents, values) if p == ""
        ]

        # Trier par valeur décroissante
        root_items.sort(key=lambda x: x[1], reverse=True)

        # Limiter au top 10 pour lisibilité
        top_items = root_items[:10]

        if not top_items:
            logger.warning("Aucun élément racine dans treemap")
            return

        # Extraire labels et valeurs
        item_labels = [item[0] for item in top_items]
        item_values = [item[1] for item in top_items]

        # Extraire couleurs depuis marker si disponibles
        colors = None
        if trace.marker and hasattr(trace.marker, 'colors'):
            colors = trace.marker.colors[:10]

        # Créer barres horizontales
        y_pos = np.arange(len(item_labels))
        ax.barh(y_pos, item_values, color=colors, alpha=0.8)

        # Configuration axes
        ax.set_yticks(y_pos)
        ax.set_yticklabels(item_labels, fontsize=10)
        ax.set_xlabel("Count", fontsize=12)
        ax.set_title(
            "Error Distribution (Top 10)", fontsize=14, fontweight='bold'
        )
        ax.grid(True, axis='x', alpha=0.3)

        # Inverser Y pour avoir le plus grand en haut
        ax.invert_yaxis()

    @staticmethod
    def _apply_layout(fig, ax, layout, is_subplot=False, axes=None):
        """Applique le layout Plotly à la figure Matplotlib."""

        # Titre global
        if layout.title:
            title_text = layout.title.text if hasattr(layout.title, 'text') else str(layout.title)
            title_text = PlotlyToMatplotlibConverter._clean_html_tags(title_text)
            if is_subplot:
                # Pour subplots, utiliser suptitle
                fig.suptitle(title_text, fontsize=16, fontweight='bold')
            else:
                # Pour figure simple, utiliser set_title sur l'axe
                ax.set_title(title_text, fontsize=16, fontweight='bold')

        # Pour subplots, pas de labels globaux (chaque subplot gère ses propres axes)
        if not is_subplot and ax is not None:
            # Labels des axes
            if layout.xaxis and hasattr(layout.xaxis, 'title'):
                xaxis_title = layout.xaxis.title
                if hasattr(xaxis_title, 'text'):
                    ax.set_xlabel(xaxis_title.text, fontsize=12)
                elif isinstance(xaxis_title, str):
                    ax.set_xlabel(xaxis_title, fontsize=12)

            if layout.yaxis and hasattr(layout.yaxis, 'title'):
                yaxis_title = layout.yaxis.title
                if hasattr(yaxis_title, 'text'):
                    ax.set_ylabel(yaxis_title.text, fontsize=12)
                elif isinstance(yaxis_title, str):
                    ax.set_ylabel(yaxis_title, fontsize=12)

            # Légende
            if layout.showlegend:
                # Vérifier qu'il y a des labels
                handles, labels = ax.get_legend_handles_labels()
                if labels:
                    ax.legend(loc='best', fontsize=10)

            # Ticks
            ax.tick_params(axis='both', labelsize=10)

            # Appliquer rotation des ticks X si configurée
            if layout.xaxis and hasattr(layout.xaxis, 'tickangle'):
                tickangle = layout.xaxis.tickangle
                if tickangle:
                    ax.tick_params(axis='x', rotation=tickangle, labelsize=10)
                    # Ajuster alignement pour angles négatifs
                    if tickangle < 0:
                        for label in ax.get_xticklabels():
                            label.set_ha('right')
                    elif tickangle > 0:
                        for label in ax.get_xticklabels():
                            label.set_ha('left')

            # Grille
            ax.grid(True, alpha=0.3, linestyle='--')

        # Ajustement automatique
        fig.tight_layout()


class PlotlyToMatplotlibSubplotConverter:
    """
    Convertisseur pour figures Plotly avec subplots.
    Utilisé pour PowerCurve, HeatMap, etc.
    """

    @staticmethod
    def convert(plotly_fig: go.Figure) -> matplotlib.figure.Figure:
        """
        Convertit une figure Plotly avec subplots en Matplotlib.

        Args:
            plotly_fig: Figure Plotly avec subplots

        Returns:
            Figure Matplotlib avec subplots équivalents
        """
        # Déterminer le nombre de subplots
        n_subplots = PlotlyToMatplotlibSubplotConverter._count_subplots(plotly_fig)

        if n_subplots <= 1:
            # Pas de subplots, utiliser le convertisseur simple
            return PlotlyToMatplotlibConverter.convert(plotly_fig)

        # Extraire dimensions
        layout = plotly_fig.layout
        width = layout.width if layout.width else 1200
        height = layout.height if layout.height else 800
        figsize = (width / 100, height / 100)

        # Créer subplots Matplotlib
        # Détecter la disposition (rows x cols)
        rows, cols = PlotlyToMatplotlibSubplotConverter._detect_grid(plotly_fig)

        fig, axes = plt.subplots(rows, cols, figsize=figsize)

        # S'assurer que axes est toujours un array 2D
        if rows == 1 and cols == 1:
            axes = np.array([[axes]])
        elif rows == 1:
            axes = axes.reshape(1, -1)
        elif cols == 1:
            axes = axes.reshape(-1, 1)

        # Grouper les traces par subplot
        traces_by_subplot = PlotlyToMatplotlibSubplotConverter._group_traces(plotly_fig)

        # Ajouter chaque trace au bon subplot
        for (row_idx, col_idx), traces in traces_by_subplot.items():
            if row_idx < rows and col_idx < cols:
                ax = axes[row_idx, col_idx]
                for trace in traces:
                    PlotlyToMatplotlibConverter._add_trace(ax, trace)

                # Appliquer styling au subplot
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.legend(loc='best', fontsize=8)

        # Titre global
        if layout.title:
            title_text = layout.title.text if hasattr(layout.title, 'text') else str(layout.title)
            fig.suptitle(title_text, fontsize=14, fontweight='bold')

        fig.tight_layout()
        return fig

    @staticmethod
    def _improve_xaxis_readability(axes):
        """
        Améliore la lisibilité des labels X (rotation si nombreux).
        Applique rotation 45° si plus de 10 labels sur l'axe X.
        """
        if not isinstance(axes, np.ndarray):
            axes = np.array([[axes]])

        for ax in axes.flatten():
            if ax is None:
                continue

            # Try/except car draw_idle() peut échouer backend Agg
            try:
                ax.figure.canvas.draw_idle()
            except Exception:
                pass  # Ignorer si backend non interactif

            x_labels = ax.get_xticklabels()
            if len(x_labels) > 10:
                ax.tick_params(axis='x', rotation=45, labelsize=8)
                for label in x_labels:
                    label.set_ha('right')

    @staticmethod
    def _count_subplots(plotly_fig: go.Figure) -> int:
        """Compte le nombre de subplots."""
        # Examiner les annotations xref/yref
        unique_refs = set()
        for trace in plotly_fig.data:
            if hasattr(trace, 'xaxis'):
                unique_refs.add(trace.xaxis)
            if hasattr(trace, 'yaxis'):
                unique_refs.add(trace.yaxis)
        return max(len(unique_refs), 1)

    @staticmethod
    def _detect_grid(plotly_fig: go.Figure) -> tuple[int, int]:
        """Détecte la disposition rows x cols."""
        # Par défaut, essayer de déduire depuis les traces
        n_subplots = PlotlyToMatplotlibSubplotConverter._count_subplots(plotly_fig)

        # Heuristique: 2 colonnes max, arrondir rows
        cols = min(n_subplots, 2)
        rows = (n_subplots + cols - 1) // cols

        return rows, cols

    @staticmethod
    def _group_traces(plotly_fig: go.Figure) -> dict:
        """Groupe les traces par subplot."""
        traces_by_subplot = {}

        for trace in plotly_fig.data:
            # Déterminer le subplot (xaxis, yaxis)
            xaxis = trace.xaxis if hasattr(trace, 'xaxis') else 'x'
            yaxis = trace.yaxis if hasattr(trace, 'yaxis') else 'y'

            # Convertir 'x', 'x2', 'x3' → indices (0, 1, 2)
            row_idx = int(yaxis.replace('y', '')) - 1 if 'y' in yaxis and len(yaxis) > 1 else 0
            col_idx = int(xaxis.replace('x', '')) - 1 if 'x' in xaxis and len(xaxis) > 1 else 0

            key = (row_idx, col_idx)
            if key not in traces_by_subplot:
                traces_by_subplot[key] = []
            traces_by_subplot[key].append(trace)

        return traces_by_subplot
