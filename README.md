# 🌍 Géocodeur Agro-Pastoral - Côte d'Ivoire

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED.svg)](https://www.docker.com/)

## 📋 Description

Outil de géocodage pour les pôles agro-pastoraux en Côte d'Ivoire. Il permet de :
- Convertir des fichiers Excel/PDF contenant des localités en fichiers géospatiaux
- Détecter automatiquement les colonnes (nom, lat/long, UTM)
- Exporter en GeoJSON, CSV, Shapefile, KML
- Faciliter la superposition avec les données du SIGFU (lotissements et permis miniers)

## 🚀 Installation

### Avec Docker (recommandé)

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/geocodeur-agro.git
cd geocodeur-agro

# Construire l'image Docker
docker compose build

# Lancer l'application
docker compose up -d

# Accéder à l'application
# http://localhost:8501

# Avec Make (si installé)
```bash

make build    # Construire
make up       # Démarrer
make down     # Arrêter
make logs     # Voir les logs
make restart  # Redémarrer
```

# Avec Docker

```bash

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

**Parfait !** Je vais te guider pas à pas pour mettre ton projet sous Git et le pousser sur un dépôt distant.

---

## 📁 Structure finale du projet

Avant de commencer, voici la structure que tu devrais avoir :

```
~/Sites/geocodeur_agro/
├── app.py                 # Application Streamlit
├── Dockerfile             # Dockerfile corrigé
├── docker-compose.yml     # Docker Compose
├── requirements.txt       # Dépendances Python
├── Makefile              # Commandes make (optionnel)
├── .dockerignore          # Fichiers exclus de Docker
├── .gitignore            # Fichiers exclus de Git (À créer)
├── data/                 # Dossier des uploads
├── output/               # Dossier des exports
└── README.md             # Documentation (À créer)
```

---

## 🔧 1. Créer le fichier `.gitignore`

Crée un fichier `.gitignore` à la racine du projet :

```bash
cd ~/Sites/geocodeur_agro
touch .gitignore
```

**Contenu du `.gitignore` :**

```gitignore
# ============================================
# Python
# ============================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
eggs/
.eggs/
parts/
var/
sdist/
develop-eggs/
.installed.cfg
lib/
lib64/
venv/
env/
ENV/
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/

# ============================================
# IDE - PhpStorm
# ============================================
.idea/
*.iml
.vscode/
*.swp
*.swo
*~
.DS_Store
.project
.pydevproject
.settings/
*.komodoproject
.komodotools/

# ============================================
# Docker
# ============================================
.docker/
docker-compose.override.yml
*.tar.gz
*.tar

# ============================================
# Données et fichiers générés
# ============================================
# Dossiers de données (mais on garde la structure)
data/*
!data/.gitkeep
output/*
!output/.gitkeep

# Fichiers temporaires
*.tmp
*.temp
*.log
*.pid
*.seed
*.pid.lock

# Fichiers de données uploadés
*.xlsx
*.xls
*.pdf
*.csv
*.geojson
*.kml
*.shp
*.shx
*.dbf
*.prj
*.cpg
*.zip

# ============================================
# Streamlit
# ============================================
.streamlit/secrets.toml
.streamlit/config.toml

# ============================================
# Système
# ============================================
.DS_Store
Thumbs.db
desktop.ini
*.bak
*.backup

# ============================================
# Fichiers sensibles
# ============================================
.env
.env.local
.env.*.local
secrets/
*.pem
*.key
*.crt
```

---

## 📝 2. Créer le fichier `README.md`

Crée un `README.md` pour documenter ton projet :

```bash
touch README.md
```

**Contenu du `README.md` :**

```markdown
# 🌍 Géocodeur Agro-Pastoral - Côte d'Ivoire

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED.svg)](https://www.docker.com/)

## 📋 Description

Outil de géocodage pour les pôles agro-pastoraux en Côte d'Ivoire. Il permet de :
- Convertir des fichiers Excel/PDF contenant des localités en fichiers géospatiaux
- Détecter automatiquement les colonnes (nom, lat/long, UTM)
- Exporter en GeoJSON, CSV, Shapefile, KML
- Faciliter la superposition avec les données du SIGFU (lotissements et permis miniers)

## 🚀 Installation

### Avec Docker (recommandé)

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/geocodeur-agro.git
cd geocodeur-agro

# Construire l'image Docker
docker compose build

# Lancer l'application
docker compose up -d

# Accéder à l'application
# http://localhost:8501
```

### Avec Make (si installé)

```bash
make build    # Construire
make up       # Démarrer
make down     # Arrêter
make logs     # Voir les logs
make restart  # Redémarrer
```

### En local (sans Docker)

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## 📊 Utilisation

1. **Upload** : Déposez un fichier Excel ou PDF
2. **Mapping** : Sélectionnez les colonnes contenant les données géographiques
3. **Traitement** : Lancez le géocodage
4. **Téléchargement** : Récupérez le fichier prêt pour QGIS

## 🛠 Technologies

- **Frontend** : Streamlit
- **Backend** : Python 3.10
- **Géospatial** : GeoPandas, Shapely, PyProj
- **Géocodage** : Geopy (Nominatim/OpenStreetMap)
- **Conteneurisation** : Docker + Docker Compose

## 📁 Structure du projet

```
geocodeur-agro/
├── app.py                 # Application principale
├── Dockerfile             # Image Docker
├── docker-compose.yml     # Orchestration
├── requirements.txt       # Dépendances Python
├── Makefile              # Commandes make
├── .dockerignore         # Fichiers exclus Docker
├── .gitignore           # Fichiers exclus Git
├── data/                 # Fichiers uploadés (ignoré par Git)
├── output/               # Fichiers générés (ignoré par Git)
└── README.md            # Documentation
```

## 🔧 Configuration

### Variables d'environnement (optionnel)

Créez un fichier `.env` :

```env
# Port d'accès
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200

# Fuseau UTM par défaut
UTM_ZONE=30
```

## 🐛 Dépannage

### Problème de permissions
```bash
sudo chown -R $USER:$USER .
```

### Port 8501 déjà utilisé
```bash
sudo lsof -i :8501
sudo kill -9 <PID>
# ou changer le port dans docker-compose.yml
```

### Logs
```bash
docker compose logs -f geocodeur
```

## 📝 License

[MIT](LICENSE)

## 👤 Auteur

**Votre Nom** - [GitHub](https://github.com/angetraore-dev)

## 🙏 Remerciements

- Ministère de l'Agriculture de Côte d'Ivoire
- OpenStreetMap pour le géocodage
- Streamlit pour le framework
```

---

## 🔄 3. Initialiser Git et faire le premier commit

### Étape 1 : Initialiser le dépôt local

```bash
cd ~/Sites/geocodeur_agro
git init
```

### Étape 2 : Ajouter les fichiers

```bash
# Voir ce qui va être ajouté
git status

# Ajouter tous les fichiers (sauf ceux dans .gitignore)
git add .

# Vérifier que .gitignore fonctionne
git status
# Tu ne devrais pas voir : data/, output/, *.pyc, .idea/, etc.
```

### Étape 3 : Créer le premier commit

```bash
git commit -m "🎉 Initial commit - Géocodeur Agro-Pastoral

- Ajout de l'application Streamlit avec géocodage
- Support Excel, PDF, Lat/Long, UTM
- Export GeoJSON, CSV
- Dockerisation complète avec Dockerfile et docker-compose
- Documentation README
"
```

---

## 🌐 4. Créer un dépôt distant

### Option A : GitHub (recommandé)

```bash
# 1. Créer un nouveau dépôt sur GitHub
# Aller sur https://github.com/new
# Nom : geocodeur-agro
# Description : Outil de géocodage pour les pôles agro-pastoraux en Côte d'Ivoire
# Public ou Private (choisis)
# Ne pas initialiser avec README (on l'a déjà)

# 2. Lier le dépôt local au dépôt distant
git remote add origin https://github.com/votre-username/geocodeur-agro.git

# 3. Pousser le code
git branch -M main
git push -u origin main
```

### Option B : GitLab

```bash
# 1. Créer un projet sur GitLab
# 2. Lier
git remote add origin https://gitlab.com/votre-username/geocodeur-agro.git
git branch -M main
git push -u origin main
```

### Option C : Bitbucket

```bash
git remote add origin https://bitbucket.org/votre-username/geocodeur-agro.git
git branch -M main
git push -u origin main
```

---

## 🔐 5. Configurer Git (si ce n'est pas déjà fait)

```bash
# Configurer ton identité
git config --global user.name "Ton Nom"
git config --global user.email "ton.email@example.com"

# (Optionnel) Configurer l'éditeur par défaut
git config --global core.editor "code --wait"  # VS Code
# ou
git config --global core.editor "vim"
```

---

## 🚀 6. Commandes Git utiles au quotidien

```bash
# Voir l'état des fichiers
git status

# Ajouter tous les fichiers modifiés
git add .

# Ajouter un fichier spécifique
git add app.py

# Faire un commit
git commit -m "📝 Description du changement"

# Pousser vers le dépôt distant
git push

# Récupérer les dernières modifications
git pull

# Voir l'historique des commits
git log --oneline --graph --all

# Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# Fusionner une branche
git checkout main
git merge feature/nouvelle-fonctionnalite
```

---

## 📋 7. Fichiers à créer pour les dossiers vides

Git ne suit pas les dossiers vides. Pour garder la structure, crée des fichiers `.gitkeep` :

```bash
# Garder la structure des dossiers
touch data/.gitkeep
touch output/.gitkeep

# Les ajouter à Git
git add data/.gitkeep output/.gitkeep
git commit -m "📁 Ajout de la structure des dossiers data/ et output/"
```

---

## 🏷️ 8. Taguer une version (optionnel)

```bash
# Créer un tag pour la version 1.0
git tag -a v1.0.0 -m "Version 1.0.0 - Version initiale stable"

# Pousser les tags
git push --tags
```

---

## 🔧 9. Vérification finale

```bash
# Voir l'état du dépôt
git status

# Voir les remotes configurés
git remote -v

# Voir l'historique
git log --oneline -5

# Vérifier que les fichiers sensibles ne sont pas trackés
git ls-files | grep -E "\.env|\.idea|__pycache__"  # Ne devrait rien afficher
```

---

## 📦 10. Si tu veux ignorer un fichier déjà tracké

Si tu as déjà commité un fichier que tu veux ignorer maintenant :

```bash
# Retirer le fichier du suivi Git mais le garder localement
git rm --cached nom_du_fichier

# Ajouter dans .gitignore
echo "nom_du_fichier" >> .gitignore

# Commit
git add .gitignore
git commit -m "🔒 Ignorer nom_du_fichier"
git push
```

---

## ✅ Checklist finale

- [ ] `.gitignore` créé avec toutes les exclusions
- [ ] `README.md` créé et bien documenté
- [ ] `git init` exécuté
- [ ] `git add .` et `git commit` faits
- [ ] Dépôt distant créé (GitHub/GitLab/Bitbucket)
- [ ] `git remote add origin ...` configuré
- [ ] `git push -u origin main` réussi
- [ ] Les fichiers `.env`, `.idea/`, `__pycache__/` ne sont pas trackés

---

## 🎯 Résumé des commandes à exécuter

```bash
# Dans l'ordre :
cd ~/Sites/geocodeur_agro

# 1. Créer le .gitignore (copier le contenu ci-dessus)
touch .gitignore

# 2. Créer le README.md (copier le contenu ci-dessus)
touch README.md

# 3. Initialiser Git
git init

# 4. Ajouter les fichiers
git add .

# 5. Premier commit
git commit -m "🎉 Initial commit - Géocodeur Agro-Pastoral"

# 6. Créer le dépôt sur GitHub (via l'interface web)

# 7. Ajouter le remote
git remote add origin https://github.com/votre-username/geocodeur-agro.git

# 8. Pousser
git branch -M main
git push -u origin main
```
