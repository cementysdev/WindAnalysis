import yaml
from typing import Any, Dict
from pathlib import Path
from src.logger_config import get_logger

logger = get_logger(__name__)

# Clés de configuration connues contenant des chemins de fichiers
PATH_KEYS = [
    'path_operation_data',
    'path_log_data',
    'template_path',
    'output_path',
    'root_path',
    'error_code_file',
]

# Extensions de fichiers à détecter pour résolution de chemins
FILE_EXTENSIONS = ['.csv', '.xlsx', '.json', '.yml', '.yaml', '.docx', '.txt', '.log']


def _should_resolve_path(key: str, value: Any) -> bool:
    """
    Détermine si une valeur doit être résolue comme chemin de fichier.

    Args:
        key: Clé du dictionnaire config
        value: Valeur associée

    Returns:
        True si la valeur doit être résolue comme chemin
    """
    if not isinstance(value, str):
        return False

    # 1. Clé spécifique de chemin
    if key in PATH_KEYS or key.endswith('_path') or 'path_' in key.lower():
        return True

    # 2. Valeur contient une extension de fichier
    if any(ext in value.lower() for ext in FILE_EXTENSIONS):
        return True

    return False


def _resolve_path(path_str: str, root: Path) -> str:
    """
    Résout un chemin relatif par rapport à root.
    Normalise les backslashes Windows pour compatibilité Linux.

    Args:
        path_str: Chemin (relatif ou absolu) depuis config.yml
        root: Dossier de base (contenant config.yml)

    Returns:
        Chemin absolu résolu
    """
    # Normaliser backslashes Windows vers forward slashes pour compatibilité multiplateforme
    normalized_path = path_str.replace('\\', '/')
    path = Path(normalized_path)

    # Si déjà absolu, retourner tel quel
    if path.is_absolute():
        return str(path)

    # Résoudre relativement à root
    resolved = (root / path).resolve()
    return str(resolved)


def _resolve_relative_paths(
    config_dict: Dict[str, Any], root: Path
) -> Dict[str, Any]:
    """
    Résout récursivement les chemins relatifs dans le dict config.

    Détecte les chemins via:
    - Clés finissant par '_path' ou contenant 'path_'
    - Valeurs contenant des extensions de fichiers (.csv, .xlsx, etc.)

    Args:
        config_dict: Dict config parsé depuis YAML
        root: Dossier de base (contenant config.yml)

    Returns:
        Dict avec chemins absolus résolus
    """
    resolved_config: Dict[str, Any] = {}

    for key, value in config_dict.items():
        if isinstance(value, dict):
            # Récursion pour les dictionnaires imbriqués
            resolved_config[key] = _resolve_relative_paths(value, root)
        elif isinstance(value, list):
            # Traiter les listes (ex: liste de turbines)
            resolved_list: list = []
            for item in value:
                if isinstance(item, dict):
                    resolved_list.append(_resolve_relative_paths(item, root))
                elif _should_resolve_path(key, item):
                    resolved_list.append(_resolve_path(item, root))
                else:
                    resolved_list.append(item)
            resolved_config[key] = resolved_list
        elif _should_resolve_path(key, value):
            # Résoudre le chemin
            original_path = value
            resolved_path = _resolve_path(value, root)
            resolved_config[key] = resolved_path

            # Log seulement si le chemin a changé
            if original_path != resolved_path:
                logger.debug(
                    f"Path resolved: {key}: {original_path} -> {resolved_path}"
                )
        else:
            # Valeur non-chemin, garder telle quelle
            resolved_config[key] = value

    return resolved_config


def build_client_config_from_scada_yaml(root: Path) -> Dict[str, Any]:
    """
    Charge et parse le fichier config.yml avec résolution des chemins relatifs.

    Tous les chemins de fichiers dans le config sont résolus comme chemins absolus
    par rapport au dossier contenant config.yml. Cela permet de charger les fichiers
    correctement que ce soit en local (experiments/) ou sur Databricks (sessions/uploaded/).

    Args:
        root: Dossier contenant config.yml

    Returns:
        Dict config avec chemins absolus résolus

    Raises:
        FileNotFoundError: Si config.yml n'existe pas dans root
        ValueError: Si config.yml n'est pas un dictionnaire YAML valide
    """
    config_path = root / "config.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Expected config.yml in {root}, but not found.")

    logger.debug(f"Loading config from: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        docs = yaml.safe_load(f)

    if not isinstance(docs, dict):
        raise ValueError(
            "Invalid config.yml format: expected a YAML mapping at the root."
        )

    # Résoudre les chemins relatifs par rapport à root
    docs = _resolve_relative_paths(docs, root)

    logger.debug(f"Config loaded and paths resolved from: {root}")

    return docs
