# 🌍 Géocodeur Agro-Pastoral - Côte d'Ivoire

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED.svg)](https://www.docker.com/)
[![GeoPandas](https://img.shields.io/badge/GeoPandas-✓-green.svg)](https://geopandas.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Description

Outil de géocodage pour les pôles agro-pastoraux en Côte d'Ivoire. Il permet de :

- ✅ Convertir des fichiers **Excel/PDF** contenant des localités en fichiers géospatiaux
- ✅ Détecter **automatiquement** les colonnes (nom, lat/long, UTM)
- ✅ Utiliser le **contexte administratif** (District, Région, Département, Sous-préfecture) pour améliorer le géocodage
- ✅ Convertir les coordonnées **DMS** (Degrés/Minutes/Secondes) en **degrés décimaux**
- ✅ **Géocoder** par nom de localité via OpenStreetMap
- ✅ **Visualiser** les points sur une carte interactive
- ✅ **Exporter** en **GeoJSON**, **CSV**, **Shapefile**, **KML**
- ✅ **Réorganiser** les colonnes de sortie dans un ordre logique
- ✅ Faciliter la **superposition** avec les données du **SIGFU** (lotissements et permis miniers)

---

## 🚀 Installation

### Avec Docker (recommandé)

```bash
# Cloner le dépôt
git clone https://github.com/angetraore-dev/geocodeur-agro.git
cd geocodeur-agro

# Construire l'image Docker
docker compose build

# Lancer l'application
docker compose up -d

# Accéder à l'application
# http://localhost:8501
```

### Avec Docker Compose (recommandé pour le développement)

```bash
# Build et lancement
docker compose up -d --build

# Voir les logs
docker compose logs -f

# Arrêter
docker compose down
```

### Installation locale (sans Docker)

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

---

## 📊 Utilisation

### 1. Upload du fichier
- Déposez un fichier **Excel (.xlsx, .xls)** ou **PDF** contenant vos données
- Taille max : 200 MB

---

### 2. Mapping des colonnes

#### Colonnes géographiques (obligatoire - au moins une)

| Colonne         | Description                                          |
|:----------------|:-----------------------------------------------------|
| **Nom du lieu** | Colonne contenant les noms des localités             |
| **Latitude**    | Colonne contenant les latitudes (décimal ou DMS)     |
| **Longitude**   | Colonne contenant les longitudes (décimal ou DMS)    |
| **X (UTM)**     | Colonne contenant les coordonnées X en mètres        |
| **Y (UTM)**     | Colonne contenant les coordonnées Y en mètres        |

#### Contexte administratif (optionnel - améliore la précision)

| Colonne             | Description                          |
|:--------------------|:-------------------------------------|
| **District**        | Colonne contenant le district        |
| **Région**          | Colonne contenant la région          |
| **Département**     | Colonne contenant le département     |
| **Sous-préfecture** | Colonne contenant la sous-préfecture |

💡 **Astuce :** Pour les petits villages non référencés, renseigner le contexte administratif permet d'obtenir de meilleurs résultats de géocodage.

---

### 3. Formats de coordonnées supportés

| Format          | Exemple                       |
|:----------------|:------------------------------|
| Degrés décimaux | `5.935111`, `-4.493972`       |
| DMS (virgule)   | `5°56'6,40"N`, `4°29'38,30"W` |
| DMS (point)     | `5°56'6.40"N`, `4°29'38.30"W` |
| UTM             | `X: 209975`, `Y: 851208`      |

---

### 4. Ordre des colonnes de sortie

L'outil réorganise automatiquement les colonnes dans un ordre logique :

| Priorité  | Colonne                              |
|:----------|:-------------------------------------|
| 1         | `N°`, `N_`, `ID`, `id`, `ROW_INDEX`  |
| 2         | `DISTRICT`, `district`               |
| 3         | `REGION`, `region`                   |
| 4         | `DEPARTEMENT`, `departement`         |
| 5         | `SOUS_PREFECTURE`, `sous_prefecture` |
| 6         | `VILLAGE`, `village`, `LOCALITE`     |
| 7         | `latitude`                           |
| 8         | `longitude`                          |
| 9         | `geometry`                           |
| 10        | Autres colonnes                      |

---

### 5. Export
L'outil propose 4 formats d'export :

| Format        | Utilisation                      |
|:--------------|:---------------------------------|
| **GeoJSON**   | Web, QGIS, Python, JavaScript    |
| **CSV**       | Excel, analyse de données        |
| **Shapefile** | QGIS, ArcGIS, SIG professionnels |
| **KML**       | Google Earth, Google Maps        |

---

## 📁 Structure du projet

```text
geocodeur-agro/
├── app.py                 # Application Streamlit
├── Dockerfile             # Image Docker
├── docker-compose.yml     # Orchestration Docker
├── requirements.txt       # Dépendances Python
├── Makefile              # Commandes make
├── .dockerignore         # Fichiers exclus de Docker
├── .gitignore            # Fichiers exclus de Git
├── data/                 # Fichiers uploadés (ignoré par Git)
├── output/               # Fichiers générés (ignoré par Git)
└── README.md            # Documentation
```

---

## 🛠 Technologies utilisées

| Technologie   | Version  | Rôle                                  |
|:--------------|:---------|:--------------------------------------|
| **Python**    | 3.10     | Langage de programmation              |
| **Streamlit** | 1.28     | Interface utilisateur                 |
| **GeoPandas** | 0.14     | Manipulation de données géospatiales  |
| **Shapely**   | 2.0      | Géométries géospatiales               |
| **PyProj**    | 3.5      | Conversion de systèmes de coordonnées |
| **Folium**    | 0.15     | Visualisation cartographique          |
| **Geopy**     | 2.3      | Géocodage (Nominatim/OpenStreetMap)   |
| **Docker**    | Latest   | Conteneurisation                      |
| **SimpleKML** | 1.3      | Export KML                            |

---

## 📋 Exemple de données

### Fichier source
```csv
N°,VILLAGE,DEPARTEMENT,REGION,LATITUDE,LONGITUDE
3284,ABOUDE DADIE,AGBOVILLE,AGNEBY-TIASSA,5°56'6,40"N,4°29'38,30"W
3285,ABOUDE VINCENT,AGBOVILLE,AGNEBY-TIASSA,5°53'31,20"N,4°36'3,60"W
3286,KOUADJAKRO,AGBOVILLE,AGNEBY-TIASSA,6°0'11,20"N,4°31'4,00"W
```

### Fichier géocodé (sortie)
```csv
N°,VILLAGE,DEPARTEMENT,REGION,latitude,longitude
3284,ABOUDE DADIE,AGBOVILLE,AGNEBY-TIASSA,5.935111,-4.493972
3285,ABOUDE VINCENT,AGBOVILLE,AGNEBY-TIASSA,5.892000,-4.601000
3286,KOUADJAKRO,AGBOVILLE,AGNEBY-TIASSA,6.003111,-4.517778
```

---

## 🐛 Dépannage

### Erreur de permissions
```bash
sudo chown -R $USER:$USER .
```

### Port 8501 déjà utilisé
```bash
# Trouver le processus
sudo lsof -i :8501
sudo kill -9 <PID>

# OU changer le port dans docker-compose.yml
ports:
  - "8502:8501"
```

### Voir les logs
```bash
docker compose logs -f geocodeur
```

### Rebuild propre
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Erreur de mémoire (Windows/WSL2)
- Augmenter la RAM dans Docker Desktop : Settings → Resources → Memory (8 GB recommandé)

### Géocodage par nom qui échoue
- Utiliser les colonnes de **contexte administratif** (Région, Département, Sous-préfecture)
- Vérifier que les noms sont correctement orthographiés
- Utiliser les coordonnées si disponibles

---

## 🔧 Variables d'environnement

```env
# Port d'accès
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200

# Fuseau UTM (Côte d'Ivoire = 30N)
UTM_ZONE=30
```

---

## 📝 License

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👤 Auteurs

**AT-DEVS**
- ✉️ **Email** : angetraore.dev@gmail.com
- 🐙 **GitHub** : [github.com/angetraore-dev](https://github.com/angetraore-dev)
- 📦 **Projet** : [github.com/angetraore-dev/geocodeur-agro](https://github.com/angetraore-dev/geocodeur-agro)
- 🛒 **Fiverr** : [fr.fiverr.com/tangeraymond](https://fr.fiverr.com/tangeraymond)

---

## 🙏 Remerciements

- **Ministère de l'Agriculture de Côte d'Ivoire** - Commande du projet
- **OpenStreetMap** - Service de géocodage
- **Streamlit** - Framework d'interface
- **GeoPandas** - Manipulation de données géospatiales

---

## 📞 Support

Pour toute question ou problème :
- 📧 Email : angetraore.dev@gmail.com
- 🐙 Issues : [github.com/angetraore-dev/geocodeur-agro/issues](https://github.com/angetraore-dev/geocodeur-agro/issues)

---

**Fait avec ❤️ en Côte d'Ivoire**
```