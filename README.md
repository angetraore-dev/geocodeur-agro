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