"""
Script pour nettoyer requirements.txt des packages non nécessaires pour Databricks Apps
"""

# Packages à exclure (nécessitent compilation ou non utilisés)
EXCLUDE_PACKAGES = {
    'psycopg2',  # PostgreSQL - non utilisé
    'jupyter',   # Jupyter notebooks - non nécessaire en production
    'jupyterlab',
    'ipykernel',
    'ipython',
    'notebook',
    'nbclient',
    'nbconvert',
    'nbformat',
    'jupyterlab_server',
    'jupyter_server',
    'jupyterlab_pygments',
    'jupyterlab_widgets',
    'jupyter_client',
    'jupyter_core',
    'jupyter-events',
    'jupyter-lsp',
    'jupyter_server_terminals',
    'ipywidgets',
    'widgetsnbextension',
    'kaleido',  # Plotly static export - optionnel
    'debugpy',  # Debug - non nécessaire en prod
    'pytest',   # Tests - non nécessaire en prod
    'pytest-timeout',
}

def clean_requirements(input_file='requirements.txt', output_file='requirements.txt'):
    """Nettoie requirements.txt des packages non nécessaires."""
    with open(input_file, 'r') as f:
        lines = f.readlines()

    cleaned_lines = []
    excluded_count = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            cleaned_lines.append(line)
            continue

        # Extraire le nom du package (avant ==, >=, etc.)
        package_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()

        if package_name.lower() in {p.lower() for p in EXCLUDE_PACKAGES}:
            print(f"❌ Exclu: {line}")
            excluded_count += 1
        else:
            cleaned_lines.append(line)

    with open(output_file, 'w') as f:
        f.write('\n'.join(cleaned_lines))

    print(f"\n✅ Nettoyage terminé!")
    print(f"   Packages exclus: {excluded_count}")
    print(f"   Packages conservés: {len([l for l in cleaned_lines if l and not l.startswith('#')])}")

if __name__ == '__main__':
    clean_requirements()
