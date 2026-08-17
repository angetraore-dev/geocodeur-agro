import streamlit as st
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import os
import re
from pathlib import Path
from shapely.geometry import Point
import pyproj
from tabula import read_pdf
import logging
import json
import tempfile
import zipfile
import io
import folium
from streamlit_folium import folium_static
import simplekml

# ============ CONFIGURATION ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Géocodeur Agro-Pastoral - Côte d'Ivoire",
    page_icon="🌍",
    layout="wide"
)

# ============ DOSSIERS ============
DATA_DIR = Path("/app/data")
OUTPUT_DIR = Path("/app/output")

try:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
except PermissionError:
    st.warning("⚠️ Impossible de créer les dossiers /app/data et /app/output. Utilisation du répertoire courant.")
    DATA_DIR = Path("data")
    OUTPUT_DIR = Path("output")
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

# ============ Fonction DE TELECHARGEMENT DANS LE FORMAT KML =============
def export_to_kml(gdf, filename):
    """
    Exporte un GeoDataFrame vers KML.

    Args:
        gdf: GeoDataFrame avec géométrie
        filename: Nom du fichier KML

    Returns:
        bytes: Contenu du fichier KML
    """
    kml = simplekml.Kml()

    for _, row in gdf.iterrows():
        point = kml.newpoint()

        # Nom du lieu
        nom = row.get('VILLAGE', row.get('village', row.get('LOCALITE', 'Sans nom')))
        point.name = str(nom)

        # Coordonnées (attention: KML utilise (lon, lat, altitude))
        point.coords = [(row.geometry.x, row.geometry.y)]

        # Ajouter des infos dans la description
        desc = []
        for col in ['VILLAGE', 'DEPARTEMENT', 'REGION', 'COMMUNE']:
            if col in row and pd.notna(row[col]):
                desc.append(f"{col}: {row[col]}")

        if desc:
            point.description = "\n".join(desc)

        # Style du point
        point.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png'
        point.style.iconstyle.scale = 1.0

    # Retourner le contenu KML en bytes
    return kml.kml().encode('utf-8')

# ============ FONCTIONS DE CONVERSION ============
def dms_to_decimal(dms_str):
    """Convertit une coordonnée DMS en degrés décimaux."""
    if not dms_str or pd.isna(dms_str):
        return None

    dms_str = str(dms_str).strip()

    try:
        return float(dms_str)
    except ValueError:
        pass

    patterns = [
        r'(\d+)°\s*(\d+)\'\s*([\d,]+)"\s*([NSWE])',
        r'(\d+)°\s*(\d+)\'\s*([\d.]+)"\s*([NSWE])',
        r'(\d+)°\s*(\d+)\s*[\']\s*([\d,]+)\s*["]\s*([NSWE])',
        r'(\d+)\s*°\s*(\d+)\s*\'\s*([\d,]+)\s*"\s*([NSWE])',
    ]

    for pattern in patterns:
        match = re.match(pattern, dms_str)
        if match:
            try:
                degrees = int(match.group(1))
                minutes = int(match.group(2))
                seconds = float(match.group(3).replace(',', '.'))
                direction = match.group(4).upper()

                decimal = degrees + (minutes / 60) + (seconds / 3600)
                return -decimal if direction in ['W', 'S'] else decimal
            except (ValueError, TypeError):
                continue

    pattern_simple = r'(\d+)°(\d+)\'([\d.]+)([NSWE])'
    match = re.match(pattern_simple, dms_str)
    if match:
        try:
            degrees = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            direction = match.group(4).upper()
            decimal = degrees + (minutes / 60) + (seconds / 3600)
            return -decimal if direction in ['W', 'S'] else decimal
        except (ValueError, TypeError):
            pass

    logger.warning(f"Impossible de convertir DMS: {dms_str}")
    return None


def convert_coordinates_if_needed(value):
    """Convertit une coordonnée DMS en décimal si nécessaire."""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    if isinstance(value, str):
        return dms_to_decimal(value)
    return None


def convert_timestamps_to_string(df):
    """Convertit les Timestamp en string pour l'export."""
    df_export = df.copy()
    for col in df_export.columns:
        if pd.api.types.is_datetime64_any_dtype(df_export[col]):
            df_export[col] = df_export[col].astype(str).replace('NaT', '')
    return df_export


def filter_output_columns(df, selected_columns):
    """Filtre les colonnes pour la sortie."""
    keep_cols = []

    for col in selected_columns:
        if col and col != "Aucune" and col in df.columns:
            keep_cols.append(col)

    id_cols = ['N°', 'N_', 'ID', 'id', 'VILLAGE', 'village', 'LOCALITE', 'localite',
               'COMMUNE', 'commune', 'DEPARTEMENT', 'departement', 'REGION', 'region']
    for col in id_cols:
        if col in df.columns and col not in keep_cols:
            keep_cols.append(col)

    if 'geometry' in df.columns:
        keep_cols.append('geometry')

    if 'latitude' in df.columns and 'latitude' not in keep_cols:
        keep_cols.append('latitude')
    if 'longitude' in df.columns and 'longitude' not in keep_cols:
        keep_cols.append('longitude')

    if not any(col in df.columns for col in id_cols):
        df['ROW_INDEX'] = df.index + 1
        keep_cols.append('ROW_INDEX')

    final_cols = [col for col in keep_cols if col in df.columns]
    return df[final_cols] if final_cols else df


def save_uploaded_file(uploaded_file):
    """Sauvegarde le fichier uploadé."""
    try:
        file_path = DATA_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
        return None


def convert_utm_to_latlon(x, y, zone=30):
    """Convertit UTM en Lat/Lon."""
    try:
        if pd.isna(x) or pd.isna(y):
            return None, None
        x, y = float(x), float(y)
        if x < 0 or y < 0:
            return None, None
        utm_proj = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84')
        lon, lat = utm_proj(x, y, inverse=True)
        return lat, lon
    except Exception as e:
        logger.warning(f"Erreur conversion UTM: {str(e)}")
        return None, None


def detect_column_mapping(df):
    """Détection automatique des colonnes."""
    suggestions = {'lieu': None, 'lat': None, 'lon': None, 'x': None, 'y': None}

    keywords = {
        'lieu': ['nom', 'localité', 'village', 'zone', 'site', 'lieu', 'commune', 'departement'],
        'lat': ['lat', 'latitude', 'y', 'northing'],
        'lon': ['lon', 'long', 'longitude', 'x', 'easting'],
        'x': ['x', 'easting', 'est', 'utm_x', 'coord_x'],
        'y': ['y', 'northing', 'north', 'utm_y', 'coord_y']
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
    """Géocode un lieu avec cache."""
    if not lieu or pd.isna(lieu):
        return None, None

    lieu_key = str(lieu).strip()
    if lieu_key in cache:
        return cache[lieu_key]

    try:
        geolocator = Nominatim(user_agent="agro_ivoire_v1")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        location = geocode(f"{lieu_key}, Côte d'Ivoire")
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


def is_dms_format(value):
    """Vérifie si une chaîne est au format DMS."""
    if not isinstance(value, str):
        return False
    return '°' in value or "'" in value


def create_map(gdf_valid):
    """Crée une carte Folium avec les points géocodés."""
    if len(gdf_valid) == 0:
        return None

    center_lat = gdf_valid.geometry.y.mean()
    center_lon = gdf_valid.geometry.x.mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

    for _, row in gdf_valid.iterrows():
        nom = row.get('VILLAGE', row.get('village', row.get('LOCALITE', 'Sans nom')))

        popup_text = f"""
        <b>{nom}</b><br>
        <b>Latitude:</b> {row.geometry.y:.6f}<br>
        <b>Longitude:</b> {row.geometry.x:.6f}
        """

        if 'DEPARTEMENT' in row:
            popup_text += f"<br><b>Département:</b> {row['DEPARTEMENT']}"
        if 'REGION' in row:
            popup_text += f"<br><b>Région:</b> {row['REGION']}"

        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=nom,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    return m


# ============ INTERFACE PRINCIPALE ============
st.title("🌍 Outil de géocodage - Pôles Agro-Pastoraux")
st.markdown("""
**Objectif** : Convertir vos données de localisation en fichiers géospatiaux exploitables
pour analyse de conflit d'usage avec le SIGFU.
""")

# Sidebar
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
    - ✅ Coordonnées Lat/Long (format décimal ou DMS)
    - ✅ Coordonnées UTM (fuseau 30N)
    """)

    st.divider()

    st.header("ℹ️ INFOS DÉVELOPPEUR")
    st.markdown("""
    **Tous droits réservés - AT-DEVS**
    - ✉️ angetraore.dev@gmail.com
    - 🐙 github.com/angetraore-dev
    - 📦 github.com/angetraore-dev/geocodeur-agro
    - 🛒 fr.fiverr.com/tangeraymond
    """)

# ============ UPLOAD ============
uploaded_file = st.file_uploader(
    "📤 Déposez votre fichier Excel ou PDF",
    type=["xlsx", "xls", "pdf"],
    help="Taille max: 200MB"
)

if uploaded_file is not None:
    saved_path = save_uploaded_file(uploaded_file)
    if saved_path:
        st.success(f"✅ Fichier sauvegardé : {saved_path}")

    # Lecture du fichier
    with st.spinner("📖 Lecture du fichier..."):
        try:
            if uploaded_file.name.endswith('.pdf'):
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

    # ============ APERÇU ============
    st.subheader("📊 Aperçu des données")
    st.dataframe(df.head(10), use_container_width=True)

    suggestions = detect_column_mapping(df)

    # ============ MAPPING ============
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
            help="Colonne contenant les latitudes (format décimal ou DMS)"
        )

        colonne_lon = st.selectbox(
            "📐 **Longitude** (si disponible)",
            options=["Aucune"] + df.columns.tolist(),
            index=(df.columns.tolist().index(suggestions['lon']) + 1) if suggestions['lon'] in df.columns else 0,
            help="Colonne contenant les longitudes (format décimal ou DMS)"
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

    # ============ OPTIONS ============
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
                options=["GeoJSON", "CSV", "Shapefile", "KML"],
                help="Format du fichier géospatial en sortie"
            )

    has_lieu = colonne_lieu is not None
    has_coords = (colonne_lat != "Aucune" and colonne_lon != "Aucune")
    has_utm = (colonne_x != "Aucune" and colonne_y != "Aucune")

    if not has_lieu and not has_coords and not has_utm:
        st.warning("⚠️ Vous devez sélectionner au moins un moyen de localisation")

    # ============ TRAITEMENT ============
    if st.button("🚀 **Lancer le géocodage**", type="primary", use_container_width=True):
        if not has_lieu and not has_coords and not has_utm:
            st.error("❌ Vous devez sélectionner au moins un moyen de localisation")
            st.stop()

        progress_bar = st.progress(0, text="Début du traitement...")
        status_text = st.empty()
        result_container = st.container()

        try:
            progress_bar.progress(10, "Préparation des données...")
            df_geo = df.copy()
            geometries = []
            geocode_status = []
            errors = []
            dms_conversions = 0

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
                            lat = convert_coordinates_if_needed(lat_val)
                            lon = convert_coordinates_if_needed(lon_val)

                            if lat is not None and lon is not None:
                                if -90 <= lat <= 90 and -180 <= lon <= 180:
                                    point = Point(lon, lat)
                                    if is_dms_format(lat_val) or is_dms_format(lon_val):
                                        dms_conversions += 1
                                        status = f"Lat/Lon (DMS→Déc): {lat:.6f}, {lon:.6f}"
                                    else:
                                        status = f"Lat/Lon: {lat:.6f}, {lon:.6f}"
                                else:
                                    errors.append(f"Ligne {index+1}: Coordonnées hors limites")
                            else:
                                errors.append(f"Ligne {index+1}: Conversion DMS échouée")
                    except (ValueError, TypeError) as e:
                        errors.append(f"Ligne {index+1}: Erreur Lat/Lon")

                # Cas 2 : Coordonnées UTM
                if point is None and has_utm:
                    try:
                        x_val = row[colonne_x]
                        y_val = row[colonne_y]
                        if pd.notna(x_val) and pd.notna(y_val):
                            lat, lon = convert_utm_to_latlon(x_val, y_val, zone_utm)
                            if lat is not None and lon is not None:
                                point = Point(lon, lat)
                                status = f"UTM → Lat: {lat:.6f}, Lon: {lon:.6f}"
                    except (ValueError, TypeError) as e:
                        errors.append(f"Ligne {index+1}: Erreur UTM")

                # Cas 3 : Géocodage par nom
                if point is None and has_lieu:
                    lieu = row[colonne_lieu]
                    if pd.notna(lieu) and str(lieu).strip():
                        status_text.text(f"🔍 Géocodage de: {lieu} ({index+1}/{total_rows})")
                        lat, lon = geocode_location(str(lieu), cache_geocode)
                        if lat is not None and lon is not None:
                            point = Point(lon, lat)
                            status = f"Géocodé: {lieu} → {lat:.6f}, {lon:.6f}"
                        else:
                            status = f"⚠️ Échec pour: {lieu}"
                            errors.append(f"Ligne {index+1}: '{lieu}' non trouvé")
                    else:
                        status = "⏭️ Lieu vide"

                geometries.append(point)
                geocode_status.append(status)

                processed += 1
                progress = 10 + int(80 * (processed / total_rows))
                progress_bar.progress(progress, f"Traitement {processed}/{total_rows}...")

            # Création du GeoDataFrame
            progress_bar.progress(95, "Création du fichier géospatial...")
            df_geo['geometry'] = geometries
            df_geo['geocode_status'] = geocode_status

            gdf = gpd.GeoDataFrame(df_geo, geometry='geometry', crs="EPSG:4326")
            gdf_valid = gdf[gdf.geometry.notna()].copy()
            gdf_invalid = gdf[gdf.geometry.isna()].copy()

            progress_bar.progress(100, "✅ Traitement terminé !")
            status_text.empty()

            # ============ RÉSULTATS ============
            with result_container:
                st.success("✅ Géocodage terminé !")

                if dms_conversions > 0:
                    st.info(f"🔄 {dms_conversions} coordonnées DMS converties en degrés décimaux")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("✅ Localités géocodées", len(gdf_valid))
                with col2:
                    st.metric("❌ Échecs", len(gdf_invalid))
                with col3:
                    st.metric("📊 Total traité", total_rows)
                with col4:
                    st.metric("🔄 DMS convertis", dms_conversions)

                if errors:
                    with st.expander(f"⚠️ Voir les {len(errors)} erreurs"):
                        for err in errors[:20]:
                            st.text(err)
                        if len(errors) > 20:
                            st.text(f"... et {len(errors) - 20} autres erreurs")

                # ============ CARTE ============
                if len(gdf_valid) > 0:
                    st.subheader("🗺️ Visualisation des points géocodés")
                    try:
                        map_obj = create_map(gdf_valid)
                        if map_obj:
                            folium_static(map_obj, width=1000, height=500)
                    except Exception as e:
                        st.warning(f"⚠️ Erreur d'affichage de la carte: {str(e)}")

                # ============ EXPORT ============
                if len(gdf_valid) > 0:
                    st.subheader("💾 Téléchargement")
                    export_filename = f"zones_geocodees_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"

                    gdf_export = convert_timestamps_to_string(gdf_valid)
                    selected_cols = [colonne_lieu, colonne_lat, colonne_lon, colonne_x, colonne_y]
                    gdf_filtered = filter_output_columns(gdf_export, selected_cols)

                    if 'latitude' not in gdf_filtered.columns:
                        gdf_filtered['latitude'] = gdf_filtered.geometry.y
                    if 'longitude' not in gdf_filtered.columns:
                        gdf_filtered['longitude'] = gdf_filtered.geometry.x

                    # GeoJSON
                    if format_export == "GeoJSON":
                        st.download_button(
                            label="📥 Télécharger en GeoJSON",
                            data=gdf_filtered.to_json(),
                            file_name=f"{export_filename}.geojson",
                            mime="application/json",
                            use_container_width=True
                        )

                    # CSV
                    elif format_export == "CSV":
                        df_csv = gdf_filtered.copy()
                        if 'geometry' in df_csv.columns:
                            df_csv = df_csv.drop(columns=['geometry'])
                        st.download_button(
                            label="📥 Télécharger en CSV",
                            data=df_csv.to_csv(index=False),
                            file_name=f"{export_filename}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    # Shapefile
                    elif format_export == "Shapefile":
                        try:
                            with tempfile.TemporaryDirectory() as tmpdir:
                                shapefile_path = os.path.join(tmpdir, f"{export_filename}.shp")
                                gdf_shape = gdf_filtered.copy()
                                for col in ['latitude', 'longitude']:
                                    if col in gdf_shape.columns:
                                        gdf_shape = gdf_shape.drop(columns=[col])
                                gdf_shape.to_file(shapefile_path, driver='ESRI Shapefile')

                                zip_buffer = io.BytesIO()
                                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                    for file in os.listdir(tmpdir):
                                        zip_file.write(os.path.join(tmpdir, file), arcname=file)

                                st.download_button(
                                    label="📥 Télécharger Shapefile (ZIP)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"{export_filename}.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                        except Exception as e:
                            st.error(f"❌ Erreur Shapefile: {str(e)}")
                            st.info("💡 Utilisez le format GeoJSON à la place")

                    # KML
                    elif format_export == "KML":
                        try:
                            gdf_kml = gdf_filtered.copy()
                            for col in ['latitude', 'longitude']:
                                if col in gdf_kml.columns:
                                    gdf_kml = gdf_kml.drop(columns=[col])

                            # Utiliser la fonction export_to_kml
                            kml_bytes = export_to_kml(gdf_kml, export_filename)

                            st.download_button(
                                label="📥 Télécharger en KML",
                                data=kml_bytes,
                                file_name=f"{export_filename}.kml",
                                mime="application/vnd.google-earth.kml+xml",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"❌ Erreur KML: {str(e)}")
                            st.info("💡 Utilisez le format GeoJSON à la place")

        except Exception as e:
            st.error(f"❌ Erreur lors du traitement : {str(e)}")
            logger.exception("Erreur détaillée:")

else:
    st.info("👆 Déposez un fichier Excel ou PDF pour commencer")

    with st.expander("ℹ️ Exemple de format attendu"):
        st.markdown("""
        **Votre fichier doit contenir au moins une de ces informations :**

        1. **Un nom de localité** (colonne comme "Village", "Localité", "Commune")
        2. **Des coordonnées Lat/Long** (colonnes "Latitude", "Longitude")
        3. **Des coordonnées UTM** (colonnes "X", "Y" en mètres)

        **Les coordonnées peuvent être :**
        - En **degrés décimaux** : `5.935111`, `-4.493972`
        - En **DMS** (Degrés/Minutes/Secondes) : `5°56'6,40"N`, `4°29'38,30"W`

        **Exemple :**
        | Village | Latitude | Longitude | X_UTM | Y_UTM |
        |---------|----------|-----------|-------|-------|
        | Bouaké  | 7.6938   | -5.0309   | 209975| 851208|
        | Yamoussoukro | 6.8276 | -5.2893 | 204752| 755421|
        """)