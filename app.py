import streamlit as st
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import os
from pathlib import Path
from shapely.geometry import Point
import pyproj
from tabula import read_pdf
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="Géocodeur Agro-Pastoral - Côte d'Ivoire",
    page_icon="🌍",
    layout="wide"
)

# ============ DOSSIERS ============
DATA_DIR = Path("/app/data")
OUTPUT_DIR = Path("/app/output")

# Créer les dossiers s'ils n'existent pas
try:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
except PermissionError:
    st.warning("⚠️ Impossible de créer les dossiers /app/data et /app/output. Utilisation du répertoire courant.")
    DATA_DIR = Path("data")
    OUTPUT_DIR = Path("output")
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

# ============ FONCTIONS UTILITAIRES ============
def save_uploaded_file(uploaded_file):
    """Sauvegarde le fichier uploadé dans data/"""
    try:
        file_path = DATA_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
        return None

def save_output_file(content, filename):
    """Sauvegarde le fichier généré dans output/"""
    try:
        file_path = OUTPUT_DIR / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
        return None

def convert_utm_to_latlon(x, y, zone=30):
    """Convertit des coordonnées UTM en Latitude/Longitude avec gestion d'erreur"""
    try:
        # Nettoyer les valeurs
        if pd.isna(x) or pd.isna(y):
            return None, None

        x = float(x)
        y = float(y)

        # Vérifier les plages UTM pour la Côte d'Ivoire
        # X typiquement entre 100000 et 1000000, Y entre 0 et 10000000
        if x < 0 or y < 0:
            return None, None

        utm_proj = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84')
        lon, lat = utm_proj(x, y, inverse=True)
        return lat, lon
    except Exception as e:
        logger.warning(f"Erreur conversion UTM: {str(e)}")
        return None, None

def detect_column_mapping(df):
    """Détection automatique des colonnes"""
    suggestions = {
        'lieu': None,
        'lat': None,
        'lon': None,
        'x': None,
        'y': None
    }

    keywords = {
        'lieu': ['nom', 'localité', 'village', 'zone', 'site', 'lieu', 'commune', 'departement', 'sous-préfecture'],
        'lat': ['lat', 'latitude', 'y', 'northing'],
        'lon': ['lon', 'long', 'longitude', 'x', 'easting'],
        'x': ['x', 'easting', 'est', 'utm_x', 'coord_x', 'x_utm'],
        'y': ['y', 'northing', 'north', 'utm_y', 'coord_y', 'y_utm']
    }

    for col in df.columns:
        col_lower = col.lower().strip()
        for key, kws in keywords.items():
            if suggestions[key] is None:
                for kw in kws:
                    if kw in col_lower:
                        suggestions[key] = col
                        break
    return suggestions

def geocode_location(lieu, cache={}):
    """Géocode un lieu avec cache et gestion d'erreur"""
    if not lieu or pd.isna(lieu):
        return None, None

    lieu_key = str(lieu).strip()

    # Vérifier le cache
    if lieu_key in cache:
        return cache[lieu_key]

    try:
        geolocator = Nominatim(user_agent="agro_ivoire_v1")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        # Essayer avec "Côte d'Ivoire" d'abord
        search_str = f"{lieu_key}, Côte d'Ivoire"
        location = geocode(search_str)

        # Si pas trouvé, essayer sans le pays
        if not location:
            location = geocode(lieu_key)

        if location:
            result = (location.latitude, location.longitude)
            cache[lieu_key] = result
            return result
        else:
            cache[lieu_key] = (None, None)
            return None, None

    except Exception as e:
        logger.error(f"Erreur géocodage pour '{lieu_key}': {str(e)}")
        cache[lieu_key] = (None, None)
        return None, None

# ============ INTERFACE PRINCIPALE ============
st.title("🌍 Outil de géocodage - Pôles Agro-Pastoraux")
st.markdown("""
**Objectif** : Convertir vos données de localisation en fichiers géospatiaux exploitables
pour analyse de conflit d'usage avec le SIGFU.
""")

# Sidebar avec instructions
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    1. **UPLOAD** : Déposez votre fichier Excel ou PDF
    2. **MAPPING** : Indiquez les colonnes contenant les données géographiques
    3. **TRAITEMENT** : Lancez le géocodage
    4. **TÉLÉCHARGEMENT** : Récupérez le fichier prêt pour QGIS
    """)

    st.divider()

    st.markdown("""
    **Formats supportés** :
    - ✅ Excel (.xlsx, .xls)
    - ✅ PDF (avec tableaux)

    **Méthodes de localisation** (au moins une) :
    - ✅ Nom du lieu (géocodage automatique)
    - ✅ Coordonnées Lat/Long
    - ✅ Coordonnées UTM (fuseau 30N)
    """)

# ÉTAPE 1 : UPLOAD
uploaded_file = st.file_uploader(
    "📤 Déposez votre fichier Excel ou PDF",
    type=["xlsx", "xls", "pdf"],
    help="Taille max: 200MB"
)

if uploaded_file is not None:

    # Sauvegarder le fichier uploadé
    saved_path = save_uploaded_file(uploaded_file)
    if saved_path:
        st.success(f"✅ Fichier sauvegardé : {saved_path}")

    # Lecture du fichier
    with st.spinner("📖 Lecture du fichier..."):
        try:
            if uploaded_file.name.endswith('.pdf'):
                # Extraire les tableaux du PDF
                tables = read_pdf(uploaded_file, pages='all', multiple_tables=False)
                if tables:
                    df = tables[0]
                    file_type = "PDF"
                else:
                    st.error("❌ Aucun tableau trouvé dans le PDF")
                    st.stop()
            else:
                df = pd.read_excel(uploaded_file)
                file_type = "Excel"
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture : {str(e)}")
            st.stop()

    st.success(f"✅ Fichier {file_type} chargé avec succès - {len(df)} lignes, {len(df.columns)} colonnes")

    # ÉTAPE 2 : PRÉVISUALISATION
    st.subheader("📊 Aperçu des données")
    st.dataframe(df.head(10), use_container_width=True)

    # Détection automatique des colonnes
    suggestions = detect_column_mapping(df)

    st.subheader("🔧 Mapping des colonnes")
    st.markdown("*Sélectionnez les colonnes correspondant aux informations géographiques*")

    col1, col2, col3 = st.columns(3)

    with col1:
        colonne_lieu = st.selectbox(
            "📍 **Nom du lieu**",
            options=df.columns.tolist(),
            index=df.columns.tolist().index(suggestions['lieu']) if suggestions['lieu'] in df.columns else 0,
            help="Colonne contenant les noms des localités à géocoder"
        )

    with col2:
        colonne_lat = st.selectbox(
            "📐 **Latitude** (si disponible)",
            options=["Aucune"] + df.columns.tolist(),
            index=(df.columns.tolist().index(suggestions['lat']) + 1) if suggestions['lat'] in df.columns else 0,
            help="Colonne contenant les latitudes en degrés décimaux"
        )

        colonne_lon = st.selectbox(
            "📐 **Longitude** (si disponible)",
            options=["Aucune"] + df.columns.tolist(),
            index=(df.columns.tolist().index(suggestions['lon']) + 1) if suggestions['lon'] in df.columns else 0,
            help="Colonne contenant les longitudes en degrés décimaux"
        )

    with col3:
        colonne_x = st.selectbox(
            "📍 **X (UTM)** (si disponible)",
            options=["Aucune"] + df.columns.tolist(),
            index=(df.columns.tolist().index(suggestions['x']) + 1) if suggestions['x'] in df.columns else 0,
            help="Colonne contenant les coordonnées X en mètres (UTM)"
        )

        colonne_y = st.selectbox(
            "📍 **Y (UTM)** (si disponible)",
            options=["Aucune"] + df.columns.tolist(),
            index=(df.columns.tolist().index(suggestions['y']) + 1) if suggestions['y'] in df.columns else 0,
            help="Colonne contenant les coordonnées Y en mètres (UTM)"
        )

    # Options avancées
    with st.expander("⚙️ Options avancées"):
        col1, col2 = st.columns(2)
        with col1:
            zone_utm = st.number_input(
                "Fuseau UTM",
                min_value=1, max_value=60, value=30,
                help="Pour la Côte d'Ivoire, le fuseau est 30N"
            )
        with col2:
            format_export = st.selectbox(
                "Format d'export",
                options=["GeoJSON", "Shapefile", "KML", "CSV"],
                help="Format du fichier géospatial en sortie"
            )

    # Vérifier qu'au moins une méthode est sélectionnée
    has_lieu = colonne_lieu is not None
    has_coords = (colonne_lat != "Aucune" and colonne_lon != "Aucune")
    has_utm = (colonne_x != "Aucune" and colonne_y != "Aucune")

    if not has_lieu and not has_coords and not has_utm:
        st.warning("⚠️ Vous devez sélectionner au moins un moyen de localisation")

    # ÉTAPE 3 : BOUTON DE TRAITEMENT
    if st.button("🚀 **Lancer le géocodage**", type="primary", use_container_width=True):

        if not has_lieu and not has_coords and not has_utm:
            st.error("❌ Vous devez sélectionner au moins un moyen de localisation")
            st.stop()

        # Barre de progression
        progress_bar = st.progress(0, text="Début du traitement...")
        status_text = st.empty()
        result_container = st.container()

        try:
            # Préparation des données
            progress_bar.progress(10, "Préparation des données...")
            df_geo = df.copy()
            geometries = []
            geocode_status = []
            errors = []

            total_rows = len(df_geo)
            processed = 0
            cache_geocode = {}

            for index, row in df_geo.iterrows():
                point = None
                status = ""

                # Cas 1 : Coordonnées Lat/Long
                if has_coords:
                    try:
                        lat_val = row[colonne_lat]
                        lon_val = row[colonne_lon]

                        if pd.notna(lat_val) and pd.notna(lon_val):
                            lat = float(lat_val)
                            lon = float(lon_val)
                            # Vérifier les plages valides
                            if -90 <= lat <= 90 and -180 <= lon <= 180:
                                point = Point(lon, lat)
                                status = f"Lat/Lon: {lat:.4f}, {lon:.4f}"
                    except (ValueError, TypeError) as e:
                        errors.append(f"Ligne {index+1}: Erreur Lat/Lon - {str(e)}")

                # Cas 2 : Coordonnées UTM
                if point is None and has_utm:
                    try:
                        x_val = row[colonne_x]
                        y_val = row[colonne_y]

                        if pd.notna(x_val) and pd.notna(y_val):
                            lat, lon = convert_utm_to_latlon(x_val, y_val, zone_utm)
                            if lat is not None and lon is not None:
                                point = Point(lon, lat)
                                status = f"UTM → Lat: {lat:.4f}, Lon: {lon:.4f}"
                    except (ValueError, TypeError) as e:
                        errors.append(f"Ligne {index+1}: Erreur UTM - {str(e)}")

                # Cas 3 : Géocodage par nom
                if point is None and has_lieu:
                    lieu = row[colonne_lieu]
                    if pd.notna(lieu) and str(lieu).strip():
                        status_text.text(f"🔍 Géocodage de: {lieu} ({index+1}/{total_rows})")
                        lat, lon = geocode_location(str(lieu), cache_geocode)
                        if lat is not None and lon is not None:
                            point = Point(lon, lat)
                            status = f"Géocodé: {lieu} → {lat:.4f}, {lon:.4f}"
                        else:
                            status = f"⚠️ Échec pour: {lieu}"
                            errors.append(f"Ligne {index+1}: '{lieu}' non trouvé")
                    else:
                        status = "⏭️ Lieu vide"

                geometries.append(point)
                geocode_status.append(status)

                # Mise à jour de la progression
                processed += 1
                progress = 10 + int(80 * (processed / total_rows))
                progress_bar.progress(progress, f"Traitement {processed}/{total_rows}...")

            # Création du GeoDataFrame
            progress_bar.progress(95, "Création du fichier géospatial...")
            df_geo['geometry'] = geometries
            df_geo['geocode_status'] = geocode_status

            gdf = gpd.GeoDataFrame(df_geo, geometry='geometry', crs="EPSG:4326")

            # Séparer les valides des invalides
            gdf_valid = gdf[gdf.geometry.notna()].copy()
            gdf_invalid = gdf[gdf.geometry.isna()].copy()

            progress_bar.progress(100, "✅ Traitement terminé !")
            status_text.empty()

            # Affichage des résultats
            with result_container:
                st.success(f"✅ Géocodage terminé !")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Localités géocodées", len(gdf_valid))
                with col2:
                    st.metric("❌ Échecs", len(gdf_invalid))
                with col3:
                    st.metric("📊 Total traité", total_rows)

                # Afficher les erreurs si présentes
                if errors:
                    with st.expander(f"⚠️ Voir les {len(errors)} erreurs"):
                        for err in errors[:20]:  # Limiter à 20 pour la lisibilité
                            st.text(err)
                        if len(errors) > 20:
                            st.text(f"... et {len(errors) - 20} autres erreurs")

                # Export
                if len(gdf_valid) > 0:
                    st.subheader("💾 Téléchargement")

                    export_filename = f"zones_geocodees_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"

                    if format_export == "GeoJSON":
                        geojson_str = gdf_valid.to_json()
                        st.download_button(
                            label="📥 Télécharger en GeoJSON",
                            data=geojson_str,
                            file_name=f"{export_filename}.geojson",
                            mime="application/json",
                            use_container_width=True
                        )

                    elif format_export == "CSV":
                        # Préparer CSV avec coordonnées explicites
                        df_csv = gdf_valid.copy()
                        df_csv['latitude'] = df_csv.geometry.y
                        df_csv['longitude'] = df_csv.geometry.x
                        df_csv = df_csv.drop(columns=['geometry'])
                        csv_str = df_csv.to_csv(index=False)
                        st.download_button(
                            label="📥 Télécharger en CSV",
                            data=csv_str,
                            file_name=f"{export_filename}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    elif format_export in ["Shapefile", "KML"]:
                        st.info(f"ℹ️ Pour {format_export}, veuillez utiliser le format GeoJSON ou CSV et convertir avec QGIS")
                        # Fallback vers GeoJSON
                        geojson_str = gdf_valid.to_json()
                        st.download_button(
                            label=f"📥 Télécharger en GeoJSON (recommandé)",
                            data=geojson_str,
                            file_name=f"{export_filename}.geojson",
                            mime="application/json",
                            use_container_width=True
                        )

        except Exception as e:
            st.error(f"❌ Erreur lors du traitement : {str(e)}")
            logger.exception("Erreur détaillée:")
else:
    # Affichage d'accueil
    st.info("👆 Déposez un fichier Excel ou PDF pour commencer")

    with st.expander("ℹ️ Exemple de format attendu"):
        st.markdown("""
        **Votre fichier doit contenir au moins une de ces informations :**

        1. **Un nom de localité** (colonne comme "Village", "Localité", "Commune")
        2. **Des coordonnées Lat/Long** (colonnes "Latitude", "Longitude")
        3. **Des coordonnées UTM** (colonnes "X", "Y" en mètres)

        **Exemple :**
        | Village | Latitude | Longitude | X_UTM | Y_UTM |
        |---------|----------|-----------|-------|-------|
        | Bouaké  | 7.6938   | -5.0309   | 209975| 851208|
        | Yamoussoukro | 6.8276 | -5.2893 | 204752| 755421|
        """)