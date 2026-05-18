import re
from pathlib import Path
from typing import Optional
import pandas as pd

from ..base_log_code import (
    BaseLogCodeManager,
    CodeCriticality,
    ErrorCode,
    FunctionalSystem,
    ResetMode,
)


class NordexN311LogCodeManager(BaseLogCodeManager):
    """
    Gestionnaire de codes d'erreur/warning pour les éoliennes NORDEX N311.

    Classification par criticité:
    - CRITICAL: DeacLevel >= 270 (arrêts immédiats, réinitialisation manuelle obligatoire)
    - HIGH: Occurrences > seuil défini ou codes répétitifs
    - MEDIUM: Avertissements, DeacLevel < 270
    - LOW: Codes informationnels

    Regroupement fonctionnel:
    - Pitch: Codes 1xxx, 5xxx (angles pales, batteries)
    - Réseau/Convertisseur: Codes 1201-1215, 300-342
    - Environnement: Codes 1002, 1005, 920 (vent, givrage)
    - Frein rotor: Codes 202, 251-270
    - Système de sécurité: Codes 5001-5203
    """

    HIGH_OCCURRENCE_THRESHOLD = 50  # Seuil pour considérer un code comme haute priorité

    # Mapping des modes de reset vers leur sévérité opérationnelle
    # Plus le score est élevé, plus l'intervention est lourde
    RESET_MODE_SEVERITY = {
        ResetMode.AUTOMATIC: 0,        # Pas d'intervention humaine
        ResetMode.SAFETY_REMOTE: 1,    # Intervention à distance possible
        ResetMode.MANUAL_AUTO: 2,      # Intervention recommandée, auto possible
        ResetMode.SAFETY_LOCAL: 3,     # Déplacement sur site requis
        ResetMode.MANUAL: 4,           # Intervention manuelle obligatoire sur site
    }

    # Mapping des plages de codes vers les systèmes fonctionnels
    SYSTEM_CODE_RANGES = {
        FunctionalSystem.PITCH: [
            (1000, 1999),  # Codes 1xxx
            (5000, 5999),  # Codes 5xxx
        ],
        FunctionalSystem.GRID_CONVERTER: [
            (1201, 1215),  # Plage spécifique réseau
            (300, 342),    # Plage convertisseur
        ],
        FunctionalSystem.ROTOR_BRAKE: [
            (202, 202),
            (251, 270),
        ],
        FunctionalSystem.SAFETY: [
            (50, 60),      # Emergency stops
            (5001, 5203),
        ],
        FunctionalSystem.VIBRATION: [
            (57, 65),      # Codes vibration
        ],
        FunctionalSystem.GENERATOR: [
            (120, 121),    # Generator cooling
        ],
        FunctionalSystem.GEARBOX: [
            (124, 124),
            (150, 162),
        ],
    }

    # Mots-clés pour identification des systèmes dans les descriptions
    SYSTEM_KEYWORDS = {
        FunctionalSystem.PITCH: ["pitch", "blade", "pale", "angle"],
        FunctionalSystem.GRID_CONVERTER: ["grid", "converter", "réseau", "convertisseur", "mcv"],
        FunctionalSystem.ENVIRONMENT: ["wind", "vent", "temperature", "temp", "ice", "givrage"],
        FunctionalSystem.ROTOR_BRAKE: ["brake", "frein", "rotor brake"],
        FunctionalSystem.SAFETY: ["emergency", "emstop", "safety", "sécurité", "sis"],
        FunctionalSystem.GENERATOR: ["gen ", "generator", "générateur", "generat"],
        FunctionalSystem.GEARBOX: ["gbx", "gearbox", "oil", "huile"],
        FunctionalSystem.VIBRATION: ["vib", "vibration", "acceleration", "acc"],
        FunctionalSystem.SYSTEM: ["plc", "system", "wtg", "hmi", "controller"],
    }

    def __init__(self, constructor_codes_path: Optional[Path] = None):
        """
        Args:
            constructor_codes_path: Chemin vers NORDEX_codes.csv.
                                   Si None, utilise le chemin par défaut.
        """
        if constructor_codes_path is None:
            # Chemin par défaut vers assets/NORDEX_codes.csv
            project_root = Path(__file__).parents[5]
            constructor_codes_path = project_root / "assets" / "NORDEX_codes.csv"

        super().__init__(constructor_codes_path)

        # Créer un index supplémentaire pour les codes sans préfixe FM
        self._create_code_aliases()

    def _create_code_aliases(self) -> None:
        """
        Crée des alias pour les codes avec/sans préfixe "FM" ou "FE".
        Permet de trouver "FM104" avec "104", "FM104", ou "FE104".

        Les fichiers de logs peuvent contenir FE au lieu de FM pour certains codes.
        """
        aliases_to_add = {}

        for code_key, error_code in list(self.error_codes.items()):
            # Si le code commence par FM, créer des alias
            if code_key.upper().startswith("FM"):
                numeric_part = code_key[2:]  # Enlever "FM"
                if numeric_part:
                    # Alias numérique pur (ex: "104")
                    if numeric_part not in self.error_codes:
                        aliases_to_add[numeric_part] = error_code

                    # Alias avec FE (ex: "FE104")
                    fe_variant = f"FE{numeric_part}"
                    if fe_variant not in self.error_codes:
                        aliases_to_add[fe_variant] = error_code

        # Ajouter les alias au dictionnaire
        self.error_codes.update(aliases_to_add)

    @staticmethod
    def normalize_code(code: str) -> str:
        """
        Normalise un code pour recherche flexible.
        Supporte: "FM104", "FE104", "104", "fm104" -> tous trouvés

        Args:
            code: Code à normaliser

        Returns:
            Code normalisé en majuscules
        """
        code_str = str(code).strip().upper()

        # Si c'est uniquement un nombre, retourner tel quel (alias créé)
        if code_str.isdigit():
            return code_str

        # Si ça commence par FM ou FE, normaliser en majuscules
        if code_str.startswith("FM") or code_str.startswith("FE"):
            return code_str

        # Sinon, retourner tel quel
        return code_str

    def _classify_codes(self) -> None:
        """Classifie tous les codes NORDEX N311 selon criticité et système fonctionnel"""
        for idx, row in self.codes_df.iterrows():
            try:
                code = str(row["Code"]).strip()
                description = str(row["Description"]).strip()

                # Conversion des niveaux en entiers, gestion des valeurs manquantes
                try:
                    reset_level = int(row["Reset Level"]) if row["Reset Level"] else 0
                except (ValueError, TypeError):
                    reset_level = 0

                try:
                    dead_level = int(row["Dead Level"]) if row["Dead Level"] else 0
                except (ValueError, TypeError):
                    dead_level = 0

                availability = str(row["Availability"]).strip()
                reset_mode = str(row["Reset Mode"]).strip()

                # Colonnes optionnelles
                brake_program = str(row.get("Brake Program", "")) if "Brake Program" in row else None
                yaw_program = str(row.get("Yaw Program", "")) if "Yaw Program" in row else None

                # Classification
                criticality = self._determine_criticality(code, dead_level, reset_level)
                functional_system = self._determine_functional_system(code, description)

                # Création de l'objet ErrorCode
                error_code = ErrorCode(
                    code=code,
                    description=description,
                    reset_level=reset_level,
                    dead_level=dead_level,
                    availability=availability,
                    reset_mode=reset_mode,
                    brake_program=brake_program,
                    yaw_program=yaw_program,
                    criticality=criticality,
                    functional_system=functional_system,
                )

                self.error_codes[code] = error_code

            except Exception as e:
                print(f"Avertissement: Impossible de traiter le code à la ligne {idx}: {e}")
                continue

    def _determine_criticality(self, code: str, dead_level: int, reset_level: int) -> CodeCriticality:
        """
        Détermine la criticité d'un code NORDEX N311.

        Règles:
        - CRITICAL: DeacLevel >= 270 (arrêt immédiat, réinitialisation manuelle)
        - MEDIUM: DeacLevel < 270
        - LOW: Codes informationnels (niveau 0 ou très bas)
        """
        # Priorité critique: DeacLevel >= 270
        if dead_level >= 270:
            return CodeCriticality.CRITICAL

        # Priorité moyenne: avertissements avec DeacLevel < 270
        if dead_level > 0 and dead_level < 270:
            return CodeCriticality.MEDIUM

        # Priorité basse: informationnels
        return CodeCriticality.LOW

    def _determine_functional_system(self, code: str, description: str) -> FunctionalSystem:
        """
        Détermine le système fonctionnel d'un code NORDEX N311.

        Utilise deux méthodes:
        1. Plages de codes numériques prédéfinies
        2. Mots-clés dans la description
        """
        # Extraction du numéro du code (FM suivi de chiffres)
        code_match = re.search(r'FM(\d+)', code)
        if code_match:
            code_number = int(code_match.group(1))

            # Vérification des plages de codes
            for system, ranges in self.SYSTEM_CODE_RANGES.items():
                for range_start, range_end in ranges:
                    if range_start <= code_number <= range_end:
                        return system

        # Analyse par mots-clés dans la description
        description_lower = description.lower()

        # Scores par système basés sur les mots-clés trouvés
        system_scores = {}
        for system, keywords in self.SYSTEM_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                system_scores[system] = score

        # Retourne le système avec le score le plus élevé
        if system_scores:
            return max(system_scores, key=system_scores.get)

        # Par défaut: OTHER
        return FunctionalSystem.OTHER

    def update_criticality_based_on_occurrences(
        self,
        code_occurrences: dict[str, int],
        high_threshold: Optional[int] = None,
    ) -> None:
        """
        Met à jour la criticité des codes en fonction de leurs occurrences.

        Les codes avec un nombre d'occurrences élevé sont promus en HIGH priority
        même si leur DeacLevel est bas, car ils révèlent une dégradation répétitive.

        Args:
            code_occurrences: Dictionnaire {code: nombre_occurrences}
            high_threshold: Seuil personnalisé pour la haute priorité
        """
        threshold = high_threshold or self.HIGH_OCCURRENCE_THRESHOLD

        for code, count in code_occurrences.items():
            if code in self.error_codes and count >= threshold:
                error_code = self.error_codes[code]
                # Promotion en HIGH si actuellement MEDIUM ou LOW
                if error_code.criticality in [CodeCriticality.MEDIUM, CodeCriticality.LOW]:
                    # Création d'un nouveau ErrorCode avec criticité mise à jour
                    updated_code = ErrorCode(
                        code=error_code.code,
                        description=error_code.description,
                        reset_level=error_code.reset_level,
                        dead_level=error_code.dead_level,
                        availability=error_code.availability,
                        reset_mode=error_code.reset_mode,
                        brake_program=error_code.brake_program,
                        yaw_program=error_code.yaw_program,
                        criticality=CodeCriticality.HIGH,
                        functional_system=error_code.functional_system,
                    )
                    self.error_codes[code] = updated_code

    def get_priority_codes_for_investigation(self) -> dict[str, list[ErrorCode]]:
        """
        Retourne les codes prioritaires nécessitant une investigation.

        Returns:
            Dictionnaire organisé par niveau de priorité
        """
        return {
            "critical": self.get_codes_by_criticality(CodeCriticality.CRITICAL),
            "high": self.get_codes_by_criticality(CodeCriticality.HIGH),
            "medium": self.get_codes_by_criticality(CodeCriticality.MEDIUM),
        }

    def get_codes_requiring_site_visit(self) -> list[ErrorCode]:
        """
        Retourne tous les codes nécessitant un déplacement sur site.

        Returns:
            Liste des codes avec reset_mode = "M" ou "SL"
        """
        return [
            code
            for code in self.error_codes.values()
            if code.reset_mode in ["M", "SL"]
        ]

    def get_unauthorized_stop_codes(self) -> list[ErrorCode]:
        """
        Retourne les codes correspondant à des arrêts non autorisés (pannes).

        Pour Nordex, un arrêt non autorisé est défini par :
        - availability = "yes" (affecte la disponibilité)
        - dead_level >= 270 (génère un arrêt immédiat)

        Cette définition se base uniquement sur les données du CSV,
        sans logique spécifique hardcodée.

        Returns:
            Liste des codes d'arrêt non autorisé
        """
        return [
            code
            for code in self.error_codes.values()
            if code.affects_availability() and code.is_critical_stop()
        ]

    def analyze_operational_impact(
        self, log_df: pd.DataFrame, code_column: str
    ) -> dict[str, any]:
        """
        Analyse l'impact opérationnel des codes d'erreur basé sur les modes de reset.

        Args:
            log_df: DataFrame contenant les logs
            code_column: Nom de la colonne contenant les codes

        Returns:
            Dictionnaire avec statistiques d'impact opérationnel
        """
        analysis = self.analyze_log_codes(log_df, code_column)

        # Classification par mode de reset
        reset_mode_distribution = {
            "automatic": [],
            "remote_reset": [],
            "manual_possible": [],
            "site_visit_required": [],
        }

        for code_str in analysis["code_occurrences"].keys():
            error_code = self.get_code(code_str)
            if error_code:
                if error_code.reset_mode == "A":
                    reset_mode_distribution["automatic"].append(code_str)
                elif error_code.reset_mode == "SR":
                    reset_mode_distribution["remote_reset"].append(code_str)
                elif error_code.reset_mode == "M(A)":
                    reset_mode_distribution["manual_possible"].append(code_str)
                elif error_code.reset_mode in ["M", "SL"]:
                    reset_mode_distribution["site_visit_required"].append(code_str)

        # Calcul du nombre de déplacements potentiels nécessaires
        site_visits_codes = reset_mode_distribution["site_visit_required"]
        total_site_visit_occurrences = sum(
            analysis["code_occurrences"].get(code, 0) for code in site_visits_codes
        )

        return {
            "reset_mode_distribution": reset_mode_distribution,
            "site_visit_codes_count": len(site_visits_codes),
            "total_site_visit_occurrences": total_site_visit_occurrences,
            "automatic_codes_count": len(reset_mode_distribution["automatic"]),
            "remote_resettable_count": len(reset_mode_distribution["remote_reset"]),
        }

    def get_owner_availability_codes(self) -> dict[str, list[ErrorCode]]:
        """
        Returns Nordex N311 codes to exclude from TBA Manufacturer calculation.

        Returns:
            Dict with three categories of codes:
                - owner_intervention: FM7 (Customer Stop)
                - curtailment: FM733 and related (noise reduction, sector management)
                - icing: FM301-692 (ice-related conditions)
        """
        owner_codes = {
            "owner_intervention": [],
            "curtailment": [],
            "icing": []
        }

        # Patterns for identification
        curtailment_keywords = ["noise", "disconnect", "sector", "curtail", "ssf"]
        icing_keywords = ["ice", "icing", "ais", "anti-icing"]

        for code in self.error_codes.values():
            code_stripped = code.code.strip().upper()
            description_lower = code.description.lower()

            # Owner intervention: explicit FM7
            if code_stripped == "FM7":
                owner_codes["owner_intervention"].append(code)

            # Curtailment: keyword matching in description
            elif any(kw in description_lower for kw in curtailment_keywords):
                owner_codes["curtailment"].append(code)

            # Icing: keyword matching in description
            elif any(kw in description_lower for kw in icing_keywords):
                owner_codes["icing"].append(code)

        return owner_codes

    def generate_report(self, log_df, code_column: str) -> str:
        """
        Génère un rapport textuel d'analyse des codes.

        Args:
            log_df: DataFrame contenant les logs
            code_column: Nom de la colonne contenant les codes

        Returns:
            Rapport formaté en texte
        """
        analysis = self.analyze_log_codes(log_df, code_column)

        report_lines = [
            "=" * 80,
            "RAPPORT D'ANALYSE DES CODES D'ERREUR - NORDEX N311",
            "=" * 80,
            "",
            f"Total de codes uniques détectés: {analysis['total_unique_codes']}",
            f"Codes connus: {analysis['known_codes_count']}",
            f"Codes inconnus: {analysis['unknown_codes_count']}",
            "",
        ]

        if analysis['unknown_codes']:
            report_lines.extend([
                "CODES INCONNUS (non documentés):",
                "-" * 80,
            ])
            for code in analysis['unknown_codes'][:10]:  # Limite à 10 pour lisibilité
                report_lines.append(f"  - {code}")
            if len(analysis['unknown_codes']) > 10:
                report_lines.append(f"  ... et {len(analysis['unknown_codes']) - 10} autres")
            report_lines.append("")

        report_lines.extend([
            "DISTRIBUTION PAR CRITICITÉ:",
            "-" * 80,
        ])
        for criticality, data in analysis['criticality_distribution'].items():
            report_lines.append(f"  {criticality.upper()}: {data['count']} codes")
        report_lines.append("")

        report_lines.extend([
            "DISTRIBUTION PAR SYSTÈME:",
            "-" * 80,
        ])
        for system, data in analysis['system_distribution'].items():
            if data['count'] > 0:
                report_lines.append(f"  {system}: {data['count']} codes")
        report_lines.append("")

        if analysis['critical_stops']:
            report_lines.extend([
                "CODES D'ARRÊT CRITIQUE DÉTECTÉS:",
                "-" * 80,
            ])
            for code in analysis['critical_stops'][:10]:
                error_code = self.get_code(code)
                if error_code:
                    report_lines.append(f"  {code}: {error_code.description}")
            report_lines.append("")

        if analysis['manual_reset_required']:
            report_lines.extend([
                "CODES NÉCESSITANT UNE RÉINITIALISATION MANUELLE:",
                "-" * 80,
            ])
            for code in analysis['manual_reset_required'][:10]:
                occurrences = analysis['code_occurrences'].get(code, 0)
                report_lines.append(f"  {code} (occurrences: {occurrences})")
            report_lines.append("")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)
