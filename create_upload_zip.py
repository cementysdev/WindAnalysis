#!/usr/bin/env python3
"""
Script helper pour créer un ZIP uploadable dans l'interface web.

Usage:
    python create_upload_zip.py <source_folder> [output_zip]

Exemple:
    python create_upload_zip.py ./experiments/scada_analyse

Le script vérifie que:
- config.yml existe à la racine
- Le sous-dossier DATA/ existe
- La structure est correcte avant de créer le ZIP
"""
import sys
import zipfile
from pathlib import Path
from typing import Optional


def create_upload_zip(
    source_folder: str,
    output_zip: Optional[str] = None
):
    """
    Crée un ZIP uploadable avec la structure attendue.

    Args:
        source_folder: Chemin du dossier source
        output_zip: Chemin du fichier ZIP de sortie (optionnel)
    """
    source_path = Path(source_folder)

    if not source_path.exists():
        print(f"[ERREUR] Erreur: Le dossier '{source_folder}' n'existe pas")
        sys.exit(1)

    if not source_path.is_dir():
        print(f"[ERREUR] Erreur: '{source_folder}' n'est pas un dossier")
        sys.exit(1)

    # Vérifier la structure
    config_file = source_path / "config.yml"
    data_folder = source_path / "DATA"

    if not config_file.exists():
        print(f"[ERREUR] Erreur: config.yml introuvable dans {source_folder}")
        print("   Le fichier config.yml doit être à la racine du dossier")
        sys.exit(1)

    if not data_folder.exists():
        print(f"[ATTENTION] Le sous-dossier DATA/ n'existe pas")
        print("L'analyse pourrait echouer sans les fichiers de donnees")

    # Nom du ZIP par défaut
    if output_zip is None:
        output_zip = f"{source_path.name}.zip"

    output_path = Path(output_zip)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[ZIP] Création du ZIP : {output_path}")
    print(f"[SRC] Source : {source_path}")
    print()

    # Créer le ZIP
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Compter les fichiers
        file_count = 0

        # Parcourir tous les fichiers
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                # Calculer le chemin relatif depuis source_path
                # Utilise relative_to pour préserver la structure interne
                arcname = file_path.relative_to(source_path)
                zipf.write(file_path, arcname)
                file_count += 1
                print(f"  + {arcname}")

    print()
    print(f"[OK] ZIP cree avec succes : {output_path}")
    print(f"[INFO] {file_count} fichiers ajoutes")
    size_mb = output_path.stat().st_size / (1024*1024)
    print(f"[SIZE] Taille: {size_mb:.2f} MB")
    print()
    print("==> Uploadez ce fichier dans l'interface web")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_upload_zip.py <source_folder> [output_zip]")
        print()
        print("Exemples:")
        print("  python create_upload_zip.py ./experiments/scada_analyse")
        print("  python create_upload_zip.py ./experiments/scada_analyse ./uploads/scada.zip")
        sys.exit(1)

    source_folder = sys.argv[1]
    output_zip = sys.argv[2] if len(sys.argv) > 2 else None

    create_upload_zip(source_folder, output_zip)
