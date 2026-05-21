# Guide de Déploiement - Wind Turbine Analytics

Ce guide couvre le déploiement de l'application sur différentes plateformes.

---

## 🏠 Déploiement Local (Développement)

### Prérequis
- Python 3.10+
- Node.js 18+
- npm ou yarn

### Installation

```bash
# 1. Backend - Installer les dépendances Python
pip install -r requirements.txt

# 2. Frontend - Installer les dépendances Node
cd frontend
npm install
cd ..

# 3. Configurer les variables d'environnement (optionnel)
cp .env.example .env
cp frontend/.env.example frontend/.env
```

### Démarrage

**Option 1 : Mode Développement (Backend et Frontend séparés)**

```bash
# Terminal 1 - Backend FastAPI
uvicorn src.wind_turbine_analytics.api.main:app --reload --port 8000

# Terminal 2 - Frontend React (avec hot reload)
cd frontend
npm run dev
```

Accéder à : http://localhost:5173

**Option 2 : Mode Production Local (Frontend servi par FastAPI)**

```bash
# Build le frontend
cd frontend
npm run build
cd ..

# Démarrer le serveur FastAPI (sert le frontend depuis dist/)
uvicorn src.wind_turbine_analytics.api.main:app --host 0.0.0.0 --port 8000
```

Accéder à : http://localhost:8000

---

## ☁️ Déploiement Databricks Apps

### Prérequis

1. **Workspace Databricks** actif (Azure/AWS/GCP)
2. **Unity Catalog Volume** créé : `/Volumes/development-bronze/wind_analytics/sessions/uploaded_data/`
3. **Databricks CLI** installé : `pip install databricks-cli`
4. **Personal Access Token** généré dans Databricks UI

### Configuration

```bash
# 1. Authentifier Databricks CLI
databricks configure --token

# Entrer :
# - Host : https://<votre-workspace>.cloud.databricks.com
# - Token : <personal-access-token>

# 2. Créer le fichier de configuration Databricks
cp .databricks/project.json.example .databricks/project.json

# Éditer project.json avec :
# - host : URL de votre workspace
# - app_path : Chemin de déploiement dans Workspace
```

### Build et Déploiement

```bash
# 1. Build complet de l'application
chmod +x build_app.sh  # Si non exécutable
./build_app.sh

# 2. Créer l'app Databricks (première fois uniquement)
databricks apps create wind-turbine-analytics \
  --description "Wind Turbine Analytics - SCADA Analysis Platform" \
  --config app.yaml

# 3. Déployer le code
databricks apps deploy wind-turbine-analytics \
  --source-path . \
  --exclude "frontend/node_modules,frontend/src,frontend/.env,*.pyc,__pycache__,tmp,tests,.git"

# 4. Démarrer l'application
databricks apps start wind-turbine-analytics

# 5. Vérifier le statut
databricks apps get wind-turbine-analytics
```

### Mise à Jour d'une App Existante

```bash
# Rebuild
./build_app.sh

# Redéployer
databricks apps deploy wind-turbine-analytics --source-path .

# Redémarrer
databricks apps restart wind-turbine-analytics
```

### Surveillance et Logs

```bash
# Voir logs en temps réel
databricks apps logs wind-turbine-analytics --follow

# Voir erreurs récentes
databricks apps logs wind-turbine-analytics --since 10m --filter ERROR

# Statut de l'app
databricks apps get wind-turbine-analytics
```

### Accès à l'Application

Une fois démarrée (status: RUNNING), l'application est accessible à :

```
https://<workspace-url>.cloud.databricks.com/apps/wind-turbine-analytics
```

**Note** : Authentification Databricks requise par défaut.

---

## 🔧 Variables d'Environnement

### Backend (`.env`)

```bash
# Chemin du volume de stockage
VOLUME_PATH=tmp  # Local
# VOLUME_PATH=/Volumes/development-bronze/wind_analytics/sessions/uploaded_data  # Databricks

# Optionnel
# API_TITLE="Wind Turbine Analytics API"
# CORS_ORIGINS=http://localhost:5173,https://custom.com
# ENABLE_AUTH=false
```

### Frontend (`frontend/.env`)

```bash
# URL de l'API en développement
VITE_API_URL=http://localhost:8000

# En production, auto-détecté depuis window.location.origin
```

### Databricks (`app.yaml`)

Les variables d'environnement Databricks sont définies dans `app.yaml` :

```yaml
env:
  VOLUME_PATH: /Volumes/development-bronze/wind_analytics/sessions/uploaded_data
  PYTHONPATH: /app
```

---

## 🐳 Déploiement Docker (Futur)

**Note** : Docker n'est pas encore configuré mais peut être ajouté facilement.

Structure suggérée :

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install Node for frontend build
RUN apt-get update && apt-get install -y nodejs npm

# Copy application
WORKDIR /app
COPY . /app

# Build frontend
RUN cd frontend && npm install && npm run build

# Install Python deps
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.wind_turbine_analytics.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📊 Validation Post-Déploiement

### Checklist

- [ ] Health check accessible : `/health`
- [ ] Documentation API accessible : `/docs`
- [ ] Upload de ZIP fonctionne
- [ ] Analyse SCADA/RunTest complète sans erreur
- [ ] Graphiques s'affichent correctement
- [ ] Tableaux avec pagination fonctionnent
- [ ] Téléchargement rapport Word OK
- [ ] Historique persiste après redémarrage
- [ ] Sessions peuvent être supprimées

### Tests Rapides

```bash
# Test health check
curl https://<url>/health

# Test upload (avec fichier test)
curl -X POST https://<url>/upload \
  -F "file=@path/to/test.zip" \
  -F "workflow_type=scada"
```

---

## 🔒 Sécurité

### Données Sensibles

- Ne jamais commiter `.env` ou `frontend/.env` (utiliser `.env.example`)
- Ne jamais commiter `.databricks/project.json` (utiliser `.example`)
- Tokens Databricks dans variables d'environnement, pas dans le code

### CORS

Par défaut, CORS autorise :
- `http://localhost:5173` (dev local)
- `https://*.databricks.com` (production Databricks)

Pour ajouter d'autres origines, modifier `src/wind_turbine_analytics/api/config.py` :

```python
cors_origins: List[str] = [
    "http://localhost:5173",
    "https://custom-domain.com",  # Ajouter ici
]
```

---

## 🆘 Troubleshooting

### Frontend ne se charge pas en production

**Problème** : Error 404 ou page blanche

**Solution** :
```bash
# Vérifier que frontend/dist/ existe
ls -la frontend/dist/

# Rebuild si nécessaire
cd frontend && npm run build
```

### Erreur "Session directory not found"

**Problème** : Sessions non persistées

**Solution** : Vérifier la variable `VOLUME_PATH`
```bash
# Local
export VOLUME_PATH=tmp

# Databricks
export VOLUME_PATH=/Volumes/development-bronze/wind_analytics/sessions/uploaded_data
```

### CORS errors dans le navigateur

**Problème** : `Access-Control-Allow-Origin` error

**Solution** : Ajouter l'origine dans `config.py` et redéployer

### Import errors au démarrage

**Problème** : `ModuleNotFoundError`

**Solution** :
```bash
# Vérifier PYTHONPATH (Databricks)
export PYTHONPATH=/app

# Ou installer deps
pip install -r requirements.txt
```

---

## 📝 Notes

- Le code métier (analyseurs, workflows) reste **100% identique** entre local et cloud
- Seuls les chemins de stockage changent (`tmp/` → Volumes)
- La configuration est centralisée via `config.py` et variables d'environnement
- Le frontend est auto-adaptatif (détecte dev vs production automatiquement)

Pour toute question, consulter :
- **Documentation API** : http://localhost:8000/docs (local)
- **CLAUDE.md** : Architecture et conventions du projet
- **README.md** : Vue d'ensemble et fonctionnalités
