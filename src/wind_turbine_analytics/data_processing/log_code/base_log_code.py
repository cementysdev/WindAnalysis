from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import pandas as pd
from enum import Enum


class CodeCriticality(Enum):
    """Criticité des codes d'erreur/warning"""

    CRITICAL = "critical"  # DeacLevel >= 270, arrêt immédiat
    HIGH = "high"  # Occurrences élevées ou problèmes répétitifs
    MEDIUM = "medium"  # Avertissements, maintenance conditionnelle
    LOW = "low"  # Informationnel


class FunctionalSystem(Enum):
    """Systèmes fonctionnels de l'éolienne"""

    PITCH = "pitch"
    GRID_CONVERTER = "grid_converter"
    ENVIRONMENT = "environment"
    ROTOR_BRAKE = "rotor_brake"
    SAFETY = "safety"
    GENERATOR = "generator"
    GEARBOX = "gearbox"
    VIBRATION = "vibration"
    SYSTEM = "system"
    OTHER = "other"


class ResetMode(Enum):
    """Modes de réinitialisation des codes d'erreur"""

    AUTOMATIC = "A"  # Réinitialisation automatique
    MANUAL = "M"  # Intervention manuelle obligatoire sur site
    SAFETY_LOCAL = "SL"  # Réinitialisation sécuritaire locale
    SAFETY_REMOTE = "SR"  # Réinitialisation sécuritaire à distance
    MANUAL_AUTO = "M(A)"  # Manuel recommandé, automatique possible sous conditions


class ErrorCode:
    """Représente un code d'erreur avec ses métadonnées"""

    def __init__(
        self,
        code: str,
        description: str,
        reset_level: int,
        dead_level: int,
        availability: str,
        reset_mode: str,
        brake_program: Optional[str] = None,
        yaw_program: Optional[str] = None,
        criticality: Optional[CodeCriticality] = None,
        functional_system: Optional[FunctionalSystem] = None,
    ):
        self.code = code
        self.description = description
        self.reset_level = reset_level
        self.dead_level = dead_level
        self.availability = availability
        self.reset_mode = reset_mode
        self.brake_program = brake_program
        self.yaw_program = yaw_program
        self.criticality = criticality
        self.functional_system = functional_system

    def __repr__(self) -> str:
        return f"ErrorCode({self.code}, criticality={self.criticality}, system={self.functional_system})"

    def is_critical_stop(self) -> bool:
        """Vérifie si le code génère un arrêt critique"""
        return self.dead_level >= 270

    def requires_manual_reset(self) -> bool:
        """Vérifie si le code nécessite une réinitialisation manuelle"""
        return self.reset_mode in ["M", "SL", "M(A)"]

    def affects_availability(self) -> bool:
        """Vérifie si le code affecte la disponibilité"""
        return self.availability.lower() == "yes"


class BaseLogCodeManager(ABC):
    """
    Classe de base pour la gestion des codes d'erreur/warning.
    Cette classe fournit la logique commune pour charger et analyser
    les codes d'erreur spécifiques à chaque type de génératrice.
    """

    def __init__(self, constructor_codes_path: Path):
        """
        Args:
            constructor_codes_path: Chemin vers le fichier CSV contenant les codes constructeur
        """
        self.constructor_codes_path = constructor_codes_path
        self.codes_df: Optional[pd.DataFrame] = None
        self.error_codes: dict[str, ErrorCode] = {}
        self._load_constructor_codes()
        self._classify_codes()

    def _load_constructor_codes(self) -> None:
        """Charge les codes d'erreur depuis le fichier constructeur"""
        try:
            self.codes_df = pd.read_csv(self.constructor_codes_path)
            self._validate_codes_dataframe()
        except Exception as e:
            raise ValueError(f"Erreur lors du chargement des codes constructeur: {e}")

    def _validate_codes_dataframe(self) -> None:
        """Valide la structure du DataFrame des codes"""
        required_columns = [
            "Code",
            "Description",
            "Reset Level",
            "Dead Level",
            "Availability",
            "Reset Mode",
        ]
        missing_columns = [
            col for col in required_columns if col not in self.codes_df.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Colonnes manquantes dans le fichier de codes: {missing_columns}"
            )

    @abstractmethod
    def _classify_codes(self) -> None:
        """
        Classifie les codes selon leur criticité et leur système fonctionnel.
        Doit être implémenté par les classes enfants pour chaque type de génératrice.
        """
        pass

    @abstractmethod
    def _determine_criticality(
        self, code: str, dead_level: int, reset_level: int
    ) -> CodeCriticality:
        """
        Détermine la criticité d'un code.
        Doit être implémenté par les classes enfants.
        """
        pass

    @abstractmethod
    def _determine_functional_system(
        self, code: str, description: str
    ) -> FunctionalSystem:
        """
        Détermine le système fonctionnel associé au code.
        Doit être implémenté par les classes enfants.
        """
        pass

    @abstractmethod
    def get_owner_availability_codes(self) -> dict[str, list[ErrorCode]]:
        """
        Returns codes to exclude from TBA Manufacturer unavailability calculation.

        These codes represent periods where the turbine is considered "available"
        from the manufacturer's perspective (owner intervention, curtailment, icing).

        Returns:
            Dict with keys:
                - "owner_intervention": Codes for manual stops by owner
                - "curtailment": Codes for aggregator demand / noise reduction
                - "icing": Codes for ice-related conditions
        """
        pass

    def _codes_match(self, code1: str, code2: str) -> bool:
        """
        Vérifie si deux codes correspondent, indépendamment du préfixe FM.

        Args:
            code1: Premier code (ex: "FM104" ou "104")
            code2: Deuxième code (ex: "FM104" ou "104")

        Returns:
            True si les codes correspondent
        """
        c1 = str(code1).strip().upper()
        c2 = str(code2).strip().upper()

        # Correspondance exacte
        if c1 == c2:
            return True

        # Extraire les parties numériques
        num1 = c1[2:] if c1.startswith("FM") else c1
        num2 = c2[2:] if c2.startswith("FM") else c2

        # Comparer les parties numériques
        return num1 == num2

    def get_code(self, code: str) -> Optional[ErrorCode]:
        """
        Récupère un code d'erreur par son identifiant.
        Supporte les formats avec ou sans préfixe (ex: "FM104" ou "104")

        Args:
            code: Code à rechercher (ex: "FM104", "104", "fm104")

        Returns:
            ErrorCode si trouvé, None sinon
        """
        code_str = str(code).strip()

        # Recherche directe
        if code_str in self.error_codes:
            return self.error_codes[code_str]

        # Recherche avec normalisation (upper case)
        code_upper = code_str.upper()
        if code_upper in self.error_codes:
            return self.error_codes[code_upper]

        # Si c'est un nombre pur, essayer avec FM devant
        if code_str.isdigit():
            fm_code = f"FM{code_str}"
            if fm_code in self.error_codes:
                return self.error_codes[fm_code]

        # Si ça commence par FM, essayer sans FM
        if code_upper.startswith("FM"):
            numeric_part = code_upper[2:]
            if numeric_part in self.error_codes:
                return self.error_codes[numeric_part]

        return None

    def get_codes_by_criticality(self, criticality: CodeCriticality) -> list[ErrorCode]:
        """Récupère tous les codes d'une criticité donnée"""
        return [
            code
            for code in self.error_codes.values()
            if code.criticality == criticality
        ]

    def get_codes_by_system(self, system: FunctionalSystem) -> list[ErrorCode]:
        """Récupère tous les codes d'un système fonctionnel donné"""
        return [
            code
            for code in self.error_codes.values()
            if code.functional_system == system
        ]

    def get_codes_by_reset_mode(self, reset_mode: str) -> list[ErrorCode]:
        """
        Récupère tous les codes nécessitant un mode de reset spécifique.

        Args:
            reset_mode: Mode de reset ("A", "M", "SL", "SR", "M(A)")

        Returns:
            Liste des codes correspondant au mode de reset
        """
        return [
            code
            for code in self.error_codes.values()
            if code.reset_mode == reset_mode
        ]

    def get_critical_stop_codes(self) -> list[ErrorCode]:
        """Récupère tous les codes générant un arrêt critique"""
        return [code for code in self.error_codes.values() if code.is_critical_stop()]

    def get_manual_intervention_codes(self) -> list[ErrorCode]:
        """
        Récupère tous les codes nécessitant une intervention humaine.

        Returns:
            Codes avec reset_mode = "M", "SL", ou "M(A)"
        """
        return [
            code
            for code in self.error_codes.values()
            if code.reset_mode in ["M", "SL", "M(A)"]
        ]

    def get_remote_resettable_codes(self) -> list[ErrorCode]:
        """
        Récupère les codes réinitialisables à distance (sans intervention sur site).

        Returns:
            Codes avec reset_mode = "A" ou "SR"
        """
        return [
            code
            for code in self.error_codes.values()
            if code.reset_mode in ["A", "SR"]
        ]

    def analyze_log_codes(
        self,
        log_df: pd.DataFrame,
        code_column: str,
    ) -> dict[str, any]:
        """
        Analyse les codes présents dans un DataFrame de logs.

        Args:
            log_df: DataFrame contenant les logs
            code_column: Nom de la colonne contenant les codes

        Returns:
            Dictionnaire avec les statistiques d'analyse
        """
        if code_column not in log_df.columns:
            raise ValueError(f"Colonne '{code_column}' introuvable dans le DataFrame")

        # Extraction des codes présents dans les logs
        log_codes = log_df[code_column].dropna().unique()

        # Identification des codes connus et inconnus
        known_codes = []
        unknown_codes = []

        for code in log_codes:
            code_str = str(code).strip()
            # Utiliser get_code pour normalisation automatique
            error_code = self.get_code(code_str)
            if error_code:
                known_codes.append(error_code)
            else:
                unknown_codes.append(code_str)

        # Comptage des occurrences
        code_counts = log_df[code_column].value_counts().to_dict()

        # Classification par criticité
        criticality_distribution = {}
        for criticality in CodeCriticality:
            codes = [c for c in known_codes if c.criticality == criticality]
            criticality_distribution[criticality.value] = {
                "count": len(codes),
                "codes": [c.code for c in codes],
            }

        # Classification par système
        system_distribution = {}
        for system in FunctionalSystem:
            codes = [c for c in known_codes if c.functional_system == system]
            system_distribution[system.value] = {
                "count": len(codes),
                "codes": [c.code for c in codes],
            }

        return {
            "total_unique_codes": len(log_codes),
            "known_codes_count": len(known_codes),
            "unknown_codes_count": len(unknown_codes),
            "unknown_codes": unknown_codes,
            "code_occurrences": code_counts,
            "criticality_distribution": criticality_distribution,
            "system_distribution": system_distribution,
            "critical_stops": [c.code for c in known_codes if c.is_critical_stop()],
            "manual_reset_required": [
                c.code for c in known_codes if c.requires_manual_reset()
            ],
        }

    def create_time_mask(
        self,
        log_df: pd.DataFrame,
        target_df: pd.DataFrame,
        code_column: str,
        log_timestamp_col: Optional[str] = None,
        log_start_col: Optional[str] = None,
        log_end_col: Optional[str] = None,
        target_timestamp_col: str = "timestamp",
        codes_to_filter: Optional[list[str]] = None,
        criticality_filter: Optional[list[CodeCriticality]] = None,
        system_filter: Optional[list[FunctionalSystem]] = None,
        reset_mode_filter: Optional[list[str]] = None,
    ) -> pd.Series:
        """
        Crée un masque booléen pour filtrer un DataFrame cible basé sur les périodes d'erreur.

        Cas d'usage:
        1. Soustraire les périodes d'erreur des données (mask = False pendant erreurs)
        2. Ne sélectionner que les périodes d'erreur (utiliser ~mask)

        Args:
            log_df: DataFrame contenant les logs d'erreur
            target_df: DataFrame à filtrer (ex: données opérationnelles)
            code_column: Nom de la colonne contenant les codes dans log_df
            log_timestamp_col: Colonne timestamp unique dans log_df (cas 1)
            log_start_col: Colonne début période dans log_df (cas 2)
            log_end_col: Colonne fin période dans log_df (cas 2)
            target_timestamp_col: Colonne timestamp dans target_df
            codes_to_filter: Liste spécifique de codes à filtrer (optionnel)
            criticality_filter: Filtrer par criticité (ex: [CodeCriticality.CRITICAL])
            system_filter: Filtrer par système (ex: [FunctionalSystem.SAFETY])
            reset_mode_filter: Filtrer par mode de reset (ex: ["M", "SL"])

        Returns:
            Série booléenne de même longueur que target_df
            True = période normale (pas d'erreur)
            False = période avec erreur

        Raises:
            ValueError: Si les colonnes temporelles ne sont pas correctement spécifiées
        """
        # Validation des paramètres temporels
        if log_timestamp_col is None and (log_start_col is None or log_end_col is None):
            raise ValueError(
                "Vous devez spécifier soit 'log_timestamp_col' "
                "soit 'log_start_col' ET 'log_end_col'"
            )

        if log_timestamp_col and (log_start_col or log_end_col):
            raise ValueError(
                "Spécifiez soit 'log_timestamp_col' soit 'log_start_col/log_end_col', pas les deux"
            )

        # Validation des colonnes
        if code_column not in log_df.columns:
            raise ValueError(f"Colonne '{code_column}' introuvable dans log_df")

        if target_timestamp_col not in target_df.columns:
            raise ValueError(
                f"Colonne '{target_timestamp_col}' introuvable dans target_df"
            )

        # Filtrer les codes selon les critères
        codes_to_mask = self._get_filtered_codes(
            codes_to_filter, criticality_filter, system_filter, reset_mode_filter
        )

        if not codes_to_mask:
            # Aucun code à filtrer, retourner tout True (aucune période à masquer)
            return pd.Series([True] * len(target_df), index=target_df.index)

        # Filtrer le log_df pour ne garder que les codes pertinents
        # Utiliser une fonction de matching flexible pour supporter FM104 et 104
        def matches_code(log_code):
            """Vérifie si un code du log correspond à un code à masquer"""
            log_code_str = str(log_code).strip()
            # Vérifier la correspondance avec tous les codes à masquer
            for target_code in codes_to_mask:
                # Normaliser les deux codes pour comparaison
                if self._codes_match(log_code_str, target_code):
                    return True
            return False

        mask_log_df = log_df[
            log_df[code_column].apply(matches_code)
        ].copy()

        if mask_log_df.empty:
            # Aucun code pertinent dans les logs
            return pd.Series([True] * len(target_df), index=target_df.index)

        # Conversion des timestamps en datetime
        target_timestamps = pd.to_datetime(target_df[target_timestamp_col])

        # Initialiser le masque à True (tout est valide par défaut)
        mask = pd.Series([True] * len(target_df), index=target_df.index)

        # Cas 1: Timestamp unique (ponctuel)
        if log_timestamp_col:
            log_timestamps = pd.to_datetime(
                mask_log_df[log_timestamp_col], format='mixed', errors='coerce'
            )

            # Marquer comme False les timestamps qui correspondent aux erreurs
            for log_ts in log_timestamps:
                if pd.notna(log_ts):
                    mask &= target_timestamps != log_ts

        # Cas 2: Période avec start et end
        else:
            log_starts = pd.to_datetime(
                mask_log_df[log_start_col], format='mixed', errors='coerce'
            )
            log_ends = pd.to_datetime(
                mask_log_df[log_end_col], format='mixed', errors='coerce'
            )

            # Pour chaque période d'erreur, marquer les timestamps correspondants
            for start, end in zip(log_starts, log_ends):
                # Ignorer les dates invalides
                if pd.notna(start) and pd.notna(end):
                    in_error_period = (target_timestamps >= start) & (
                        target_timestamps <= end
                    )
                    mask &= ~in_error_period

        return mask

    def _get_filtered_codes(
        self,
        codes_to_filter: Optional[list[str]],
        criticality_filter: Optional[list[CodeCriticality]],
        system_filter: Optional[list[FunctionalSystem]],
        reset_mode_filter: Optional[list[str]],
    ) -> list[str]:
        """
        Récupère la liste des codes à filtrer selon les critères.

        Args:
            codes_to_filter: Liste explicite de codes
            criticality_filter: Filtrer par criticité
            system_filter: Filtrer par système
            reset_mode_filter: Filtrer par mode de reset

        Returns:
            Liste des codes correspondant aux critères
        """
        # Si une liste explicite est fournie, l'utiliser directement
        if codes_to_filter is not None:
            return codes_to_filter

        # Sinon, construire la liste selon les filtres
        filtered_codes = []

        # Filtrage par criticité
        if criticality_filter:
            for criticality in criticality_filter:
                codes = self.get_codes_by_criticality(criticality)
                filtered_codes.extend([c.code for c in codes])

        # Filtrage par système
        if system_filter:
            for system in system_filter:
                codes = self.get_codes_by_system(system)
                filtered_codes.extend([c.code for c in codes])

        # Filtrage par mode de reset
        if reset_mode_filter:
            for mode in reset_mode_filter:
                codes = self.get_codes_by_reset_mode(mode)
                filtered_codes.extend([c.code for c in codes])

        # Si aucun filtre spécifié, utiliser tous les codes
        if not criticality_filter and not system_filter and not reset_mode_filter:
            filtered_codes = list(self.error_codes.keys())

        # Supprimer les doublons
        return list(set(filtered_codes))

    def filter_by_codes(
        self,
        target_df: pd.DataFrame,
        log_df: pd.DataFrame,
        code_column: str,
        log_timestamp_col: Optional[str] = None,
        log_start_col: Optional[str] = None,
        log_end_col: Optional[str] = None,
        target_timestamp_col: str = "timestamp",
        codes_to_filter: Optional[list[str]] = None,
        criticality_filter: Optional[list[CodeCriticality]] = None,
        system_filter: Optional[list[FunctionalSystem]] = None,
        reset_mode_filter: Optional[list[str]] = None,
        exclude_error_periods: bool = True,
    ) -> pd.DataFrame:
        """
        Filtre un DataFrame en fonction des périodes d'erreur.

        Args:
            target_df: DataFrame à filtrer
            log_df: DataFrame contenant les logs d'erreur
            code_column: Colonne des codes dans log_df
            log_timestamp_col: Colonne timestamp dans log_df (cas ponctuel)
            log_start_col: Colonne début période dans log_df
            log_end_col: Colonne fin période dans log_df
            target_timestamp_col: Colonne timestamp dans target_df
            codes_to_filter: Codes spécifiques à filtrer
            criticality_filter: Filtrer par criticité
            system_filter: Filtrer par système
            reset_mode_filter: Filtrer par mode de reset
            exclude_error_periods: Si True, exclut les périodes d'erreur (par défaut).
                                  Si False, ne garde QUE les périodes d'erreur.

        Returns:
            DataFrame filtré

        Example:
            # Exclure les périodes avec des codes critiques
            clean_data = manager.filter_by_codes(
                target_df=operation_df,
                log_df=log_df,
                code_column='operator_code',
                log_start_col='start_date',
                log_end_col='end_date',
                criticality_filter=[CodeCriticality.CRITICAL],
                exclude_error_periods=True
            )

            # Ne garder QUE les périodes avec des codes de vibration
            vib_data = manager.filter_by_codes(
                target_df=operation_df,
                log_df=log_df,
                code_column='operator_code',
                log_start_col='start_date',
                log_end_col='end_date',
                system_filter=[FunctionalSystem.VIBRATION],
                exclude_error_periods=False
            )

            # Exclure les périodes nécessitant intervention manuelle
            auto_data = manager.filter_by_codes(
                target_df=operation_df,
                log_df=log_df,
                code_column='operator_code',
                log_start_col='start_date',
                log_end_col='end_date',
                reset_mode_filter=["M", "SL"],
                exclude_error_periods=True
            )
        """
        mask = self.create_time_mask(
            log_df=log_df,
            target_df=target_df,
            code_column=code_column,
            log_timestamp_col=log_timestamp_col,
            log_start_col=log_start_col,
            log_end_col=log_end_col,
            target_timestamp_col=target_timestamp_col,
            codes_to_filter=codes_to_filter,
            criticality_filter=criticality_filter,
            system_filter=system_filter,
            reset_mode_filter=reset_mode_filter,
        )

        if exclude_error_periods:
            # Garder les périodes normales (mask = True)
            return target_df[mask].copy()
        else:
            # Garder les périodes d'erreur (mask = False)
            return target_df[~mask].copy()

    def get_codes_summary(self) -> dict[str, any]:
        """Retourne un résumé de tous les codes chargés"""
        return {
            "total_codes": len(self.error_codes),
            "by_criticality": {
                crit.value: len(self.get_codes_by_criticality(crit))
                for crit in CodeCriticality
            },
            "by_system": {
                sys.value: len(self.get_codes_by_system(sys))
                for sys in FunctionalSystem
            },
            "critical_stops_count": len(self.get_critical_stop_codes()),
        }
