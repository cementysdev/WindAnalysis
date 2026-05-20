# Wind Turbine Analytics 🌬️

**Système complet d'analyse de performance pour parcs éoliens avec interface web moderne**

Plateforme d'analyse avancée qui génère automatiquement des rapports Word professionnels à partir de données SCADA et logs d'alarme. Inclut une interface web interactive pour upload, configuration et visualisation en temps réel.

---

## 🌟 Nouveautés - Interface Web

Une interface web complète pour faciliter l'utilisation :

- 🖥️ **Dashboard interactif** : Visualisation en temps réel des résultats d'analyse
- 📤 **Upload par glisser-déposer** : Import simplifié de fichiers SCADA et logs
- ⚙️ **Configuration guidée** : Assistant pas-à-pas pour configurer l'analyse
- 📊 **Graphiques interactifs** : Visualisations Plotly.js zoomables et exportables
- 📜 **Historique des analyses** : Consultation et gestion des sessions précédentes (pagination 10 par page)
- 🚀 **Lazy loading** : Chargement optimisé des sections pour performances maximales
- 📱 **Responsive** : Interface adaptée desktop et tablette

**Workflows supportés** :
- 🔵 **SCADA** : Analyse continue de performance opérationnelle
- 🟢 **RunTest** : Validation de mise en service (5 critères IEC)

---

## 🎯 Analyse SCADA - Performance Continue

Analyse approfondie des performances opérationnelles sur périodes étendues :

- 📊 **EBA (Energy-Based Availability)** : Disponibilité énergétique mensuelle selon IEC 61400-26
- 🕒 **TBA (Time-Based Availability)** : Disponibilité temporelle avec gestion des arrêts
- 📈 **Courbes de puissance normatives** : Conformité IEC 61400-12-2 avec correction densité
- 🌡️ **Analyse environnementale** : Rose des vents, rose des puissances, calibration direction
- ⚠️ **Analyse des codes d'erreur** : Criticité, fréquence, durée d'impact, top erreurs récurrentes
- 📉 **Pertes de production** : Identification des sources de perte et quantification énergétique
- 🎯 **Tip Speed Ratio** : Analyse de la vitesse de bout de pale et optimisation aérodynamique

**Livrables** : Rapports Word automatisés, visualisations interactives web, export JSON/PNG, recommandations d'optimisation.

---

## 🧪 Analyse RunTest - Validation Mise en Service

Validation complète de la recette finale selon 5 critères IEC :

1. ⏱️ **120 heures consécutives** : Fonctionnement continu sans arrêt critique
2. ⚡ **Cut-in à cut-out** : Validation de la plage opérationnelle complète
3. 🔋 **Puissance nominale** : Maintien ≥ 97% Pnom pendant durée requise
4. 🔄 **Autonomie d'exploitation** : ≤ 3 redémarrages manuels locaux
5. ✅ **Disponibilité** : ≥ 92% sur la période de test

**Livrables** : Certificat de validation, rapport de conformité, tableau de bord des critères, chronologie des événements.

---

## 📊 Visualisations Générées

### Rose des Vents
<img src="./docs/wind_rose_chart.png" width="500" alt="Rose des vents" />

Distribution directionnelle des vents avec bins de vitesse (0-3, 3-5, 5-10, 10-15+ m/s).

### Courbe de Puissance
<img src="./docs/power_curve_chart.png" width="500" alt="Courbe de puissance" />

Relation vitesse du vent vs puissance active avec seuils de validation.

### EBA Mensuelle - Constructeur
<img src="./docs/eba_manufacturer.png" width="500" alt="EBA Manufacturer" />

Disponibilité énergétique mensuelle par turbine avec codes couleur de performance.

### Pertes d'Énergie Mensuelles
<img src="./docs/eba_cut_in_cut_out_chart.png" width="500" alt="Pertes EBA" />

Histogramme des pertes d'énergie par turbine avec gradient de criticité (bleu → rouge).

### Top Codes d'Erreur
<img src="./docs/top_error_frequency.png" width="500" alt="Top erreurs" />

Top 10 des codes par fréquence et durée avec criticité colorée (CRITICAL, HIGH, MEDIUM, LOW).

### Répartition des Erreurs (Treemap)
<img src="./docs/error_code_treemap.png" width="500" alt="Treemap erreurs" />

Arborescence hiérarchique des codes d'erreur par système fonctionnel et criticité.

---

## 🚀 Démarrage Rapide

### Installation Backend (Python)
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Installation Frontend (React)
```bash
cd frontend
npm install
```

### Lancer l'Application Complète

**Option 1 : Interface Web (Recommandé)**
```bash
# Terminal 1 - Backend API (FastAPI)
uvicorn src.wind_turbine_analytics.api.main:app --reload --port 8000

# Terminal 2 - Frontend React
cd frontend
npm run dev
```
Puis ouvrir http://localhost:5173 dans votre navigateur.

**Option 2 : Ligne de Commande**
```bash
# Analyse SCADA
python scada_main.py ./experiments/scada_analyse

# Analyse RunTest
python runtest_main.py ./experiments/runtest_example
```

### Configuration YAML
Fichiers dans `experiments/*/config.yml` définissent :
- **Chemins** : CSV SCADA + logs d'alarme
- **Période** : date_range (start/end)
- **Critères** : Seuils EBA, puissance nominale, disponibilité
- **Mapping colonnes** : Adapté au format constructeur (Nordex, Vestas, etc.)
- **Template** : Word + destination rapport généré

---

## 📁 Structure du Projet

```
WindAnalysis/
├── frontend/                          # Interface Web React + TypeScript
│   ├── src/
│   │   ├── components/               # Composants React
│   │   │   ├── wizard/              # Assistant de configuration
│   │   │   ├── results/             # Affichage des résultats (lazy loading)
│   │   │   ├── sessions/            # Gestion de l'historique
│   │   │   └── shared/              # Composants réutilisables
│   │   ├── pages/                   # Pages principales
│   │   ├── services/                # API client (axios)
│   │   └── types/                   # Types TypeScript
│   └── package.json
│
├── src/wind_turbine_analytics/
│   ├── api/                          # Backend FastAPI
│   │   ├── main.py                  # Point d'entrée API
│   │   ├── routes/                  # Endpoints REST
│   │   └── services/                # Logique métier API
│   ├── application/                  # Workflows & configuration
│   │   ├── workflows/               # ScadaWorkflow, RuntestWorkflow
│   │   ├── configuration/           # Modèles de config YAML
│   │   └── utils/                   # Chargement données, validation
│   ├── data_processing/              # Moteur d'analyse
│   │   ├── analyzer/                # 15+ analyseurs spécialisés
│   │   ├── visualizer/              # Générateurs de graphiques Plotly
│   │   ├── tabler/                  # Générateurs de tableaux
│   │   └── log_code/                # Gestion codes d'erreur constructeurs
│   └── presentation/                 # Génération rapports Word
│
├── experiments/                      # Configurations & données de test
├── assets/                           # Templates Word & codes CSV
├── output/                           # Rapports et sessions générés
├── tests/                            # Tests unitaires pytest
└── docs/                             # Documentation & visuels
```

---

## 🛠️ Stack Technologique

### Backend
- **Python 3.10+** : Langage principal
- **FastAPI** : API REST moderne et performante
- **Pandas** : Traitement des séries temporelles SCADA (millions de lignes)
- **NumPy** : Calculs scientifiques et statistiques
- **Plotly** : Visualisations interactives (PNG + JSON)
- **python-docx** : Génération automatique de rapports Word
- **pytest** : Tests unitaires et validation continue

### Frontend
- **React 18** : Framework UI moderne avec hooks
- **TypeScript** : Typage statique pour robustesse
- **Vite** : Build tool ultra-rapide
- **TailwindCSS** : Framework CSS utilitaire
- **Plotly.js** : Rendu des graphiques interactifs
- **Axios** : Client HTTP pour API REST
- **Lucide React** : Icônes SVG optimisées

### Optimisations Frontend
- ⚡ **Lazy loading** : Chargement à la demande des sections (réduction 10x DOM nodes)
- 💾 **Cache intelligent** : Mise en cache des données chargées
- 📄 **Pagination** : 10 items par page sur historique
- 🎨 **Responsive design** : Interface adaptée tous écrans

---

## 🔧 Fonctionnalités Avancées

### Interface Web
- **Assistant de configuration** : 3 étapes guidées (Upload → Config → Analyse → Résultats)
- **Prévisualisation des données** : Vérification des fichiers uploadés avant analyse
- **Sidebar intelligente** : Navigation par section avec compteurs dynamiques
- **Export multi-format** : Word, JSON, PNG (graphiques haute résolution)
- **Gestion des sessions** : Sauvegarde automatique, consultation historique, suppression batch

### Analyseurs Spécialisés
- **EBA/TBA** : Disponibilité énergétique et temporelle avec codes constructeurs
- **Calibration vent** : Vérification écart nacelle/anémomètre (critère ≤ 5°)
- **Codes d'erreur** : Classification par criticité (CRITICAL → LOW) et système
- **Normative IEC** : Correction densité air + exclusion bridage/sillage
- **120h consécutives** : Détection plages opérationnelles continues

### Backend API
- **Upload multipart** : Gestion fichiers ZIP volumineux (100+ MB)
- **Validation robuste** : Vérification YAML, CSV, mapping colonnes
- **Sessions persistantes** : Stockage structure JSON + fichiers
- **Endpoints REST** : `/analyze`, `/sessions`, `/download`, `/delete`
- **CORS configuré** : Accès frontend cross-origin

---

## 📖 Documentation Complémentaire

- [Visualiseur EBA](./docs/EBA_VISUALIZER.md) : Guide complet des visualisations de disponibilité énergétique
- [CLAUDE.md](./CLAUDE.md) : Architecture technique et conventions de développement
- [API Documentation](http://localhost:8000/docs) : Documentation interactive Swagger (backend démarré)

---

## 🐛 Résolution de Problèmes

### Backend ne démarre pas
```bash
# Vérifier la version Python
python --version  # Doit être >= 3.10

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

### Frontend erreurs de compilation
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port 8000 déjà utilisé
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

**Développé pour l'analyse de performance de parcs éoliens Nordex, Vestas, Siemens Gamesa.**
**Conforme IEC 61400-12-2, IEC 61400-26, normes de validation constructeurs.**
