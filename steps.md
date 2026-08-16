Parfait ! On va donc construire **l'application Python complète** avec Streamlit. Je vais te donner une version **prête à l'emploi**, robuste, avec toutes les fonctionnalités dont ton ami aura besoin.

---

## 🚀 L'application complète

Voici le fichier `app.py` complet. Je l'ai structuré pour qu'il soit :
- **Modulaire** (facile à modifier)
- **Robuste** (gestion des erreurs)
- **Pro** (barre de progression, logs, exports multiples)

---

### 📁 app.py (Code complet)

```python
import streamlit as st
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pyproj
from shapely.geometry import Point
import time
import io
import base64
from pathlib import Path
import tempfile
import os

# Configuration de la page
st.set_page_config(
    page_title="Géocodeur Agro-Pastoral - Côte d'Ivoire",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache pour ne pas re-géocoder plusieurs fois
@st.cache_data
def geocode_location(lieu):
    """Géocode un lieu avec cache"""
    geolocator = Nominatim(user_agent="agro_ivoire_v1")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    try:
        location = geocode(f"{lieu}, Côte d'Ivoire")
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        st.warning(f"Erreur pour {lieu}: {str(e)}")
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
    
    # Mots-clés pour chaque type
    keywords = {
        'lieu': ['nom', 'localité', 'village', 'zone', 'site', 'lieu', 'commune', 'departement', 'sous-préfecture'],
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

def convert_utm_to_latlon(x, y, zone=30):
    """Convertit des coordonnées UTM en Latitude/Longitude"""
    try:
        utm_proj = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', south=False)
        lon, lat = utm_proj(x, y, inverse=True)
        return lat, lon
    except Exception as e:
        st.warning(f"Erreur conversion UTM: {str(e)}")
        return None, None

def process_file(uploaded_file):
    """Lecture du fichier Excel ou PDF"""
    file_extension = Path(uploaded_file.name).suffix.lower()
    
    try:
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(uploaded_file)
            return df, "Excel"
        elif file_extension == '.pdf':
            try:
                import tabula
                tables = tabula.read_pdf(uploaded_file, pages='all', multiple_tables=False)
                if tables:
                    df = tables[0]
                    return df, "PDF"
                else:
                    st.error("Aucun tableau trouvé dans le PDF")
                    return None, None
            except ImportError:
                st.error("Bibliothèque tabula-py non installée. Installez-la avec: pip install tabula-py")
                return None, None
        else:
            st.error(f"Format {file_extension} non supporté")
            return None, None
    except Exception as e:
        st.error(f"Erreur de lecture: {str(e)}")
        return None, None

def main():
    # Titre et description
    st.title("🌍 Outil de Géocodage - Pôles Agro-Pastoraux")
    st.markdown("""
    **Objectif** : Convertir vos données de localisation (villages, coordonnées) en fichiers géospatiaux 
    exploitables pour analyse de conflit d'usage avec le SIGFU.
    """)
    
    # Sidebar avec instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **UPLOAD** : Déposez votre fichier Excel ou PDF
        2. **MAPPING** : Indiquez quelles colonnes contiennent les données géographiques
        3. **TRAITEMENT** : Lancez le géocodage
        4. **TÉLÉCHARGEMENT** : Récupérez le fichier prêt pour QGIS
        """)
        
        st.divider()
        
        st.markdown("""
        **Formats supportés** :
        - ✅ Excel (.xlsx, .xls)
        - ✅ PDF (avec tableaux)
        
        **Systèmes de coordonnées** :
        - ✅ Degrés décimaux (Lat/Long)
        - ✅ UTM (X/Y en mètres)
        - ✅ Géocodage par nom
        """)
    
    # Zone d'upload
    uploaded_file = st.file_uploader(
        "📤 Déposez votre fichier ici",
        type=['xlsx', 'xls', 'pdf'],
        help="Taille max: 200MB"
    )
    
    if uploaded_file is not None:
        # Lecture du fichier
        with st.spinner("📖 Lecture du fichier..."):
            df, file_type = process_file(uploaded_file)
        
        if df is not None:
            # Informations sur le fichier
            st.success(f"✅ Fichier {file_type} chargé avec succès - {len(df)} lignes, {len(df.columns)} colonnes")
            
            # Aperçu des données
            st.subheader("📊 Aperçu des données")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(df.head(10), use_container_width=True)
            with col2:
                st.caption(f"**Colonnes disponibles** :")
                for i, col in enumerate(df.columns):
                    st.caption(f"{i+1}. {col}")
            
            # Détection automatique des colonnes
            suggestions = detect_column_mapping(df)
            
            # Interface de mapping
            st.subheader("🔧 Configuration du géocodage")
            st.markdown("*Sélectionnez les colonnes correspondant aux informations géographiques*")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                colonne_lieu = st.selectbox(
                    "📍 **Nom du lieu** (ville/village/zone)",
                    options=df.columns.tolist(),
                    index=df.columns.tolist().index(suggestions['lieu']) if suggestions['lieu'] in df.columns else 0,
                    help="Colonne contenant les noms des localités à géocoder"
                )
            
            with col2:
                st.markdown("**Coordonnées (optionnel)**")
                colonne_lat = st.selectbox(
                    "Latitude (si disponible)",
                    options=["Aucune"] + df.columns.tolist(),
                    index=(df.columns.tolist().index(suggestions['lat']) + 1) if suggestions['lat'] in df.columns else 0,
                    help="Colonne contenant les latitudes en degrés décimaux"
                )
                
                colonne_lon = st.selectbox(
                    "Longitude (si disponible)",
                    options=["Aucune"] + df.columns.tolist(),
                    index=(df.columns.tolist().index(suggestions['lon']) + 1) if suggestions['lon'] in df.columns else 0,
                    help="Colonne contenant les longitudes en degrés décimaux"
                )
            
            with col3:
                st.markdown("**Coordonnées UTM (optionnel)**")
                colonne_x = st.selectbox(
                    "X (Easting)",
                    options=["Aucune"] + df.columns.tolist(),
                    index=(df.columns.tolist().index(suggestions['x']) + 1) if suggestions['x'] in df.columns else 0,
                    help="Colonne contenant les coordonnées X en mètres (UTM)"
                )
                
                colonne_y = st.selectbox(
                    "Y (Northing)",
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
                        options=["GeoJSON", "Shapefile", "KML"],
                        help="Format du fichier géospatial en sortie"
                    )
            
            # Bouton de traitement
            if st.button("🚀 **Lancer le géocodage**", type="primary", use_container_width=True):
                
                # Vérification des colonnes sélectionnées
                has_lieu = colonne_lieu is not None
                has_coords = (colonne_lat != "Aucune" and colonne_lon != "Aucune")
                has_utm = (colonne_x != "Aucune" and colonne_y != "Aucune")
                
                if not has_lieu and not has_coords and not has_utm:
                    st.error("❌ Vous devez sélectionner au moins un moyen de localisation (nom, Lat/Long, ou UTM)")
                    return
                
                # Barre de progression
                progress_bar = st.progress(0, text="Début du traitement...")
                status_text = st.empty()
                
                # Préparation des données
                progress_bar.progress(10, "Préparation des données...")
                df_geo = df.copy()
                geometries = []
                geocode_results = []
                
                total_rows = len(df_geo)
                processed = 0
                
                for index, row in df_geo.iterrows():
                    point = None
                    geocode_info = ""
                    
                    # Cas 1 : Coordonnées Lat/Long
                    if has_coords:
                        try:
                            lat = float(row[colonne_lat]) if pd.notna(row[colonne_lat]) else None
                            lon = float(row[colonne_lon]) if pd.notna(row[colonne_lon]) else None
                            if lat is not None and lon is not None:
                                point = Point(lon, lat)
                                geocode_info = f"Lat/Lon: {lat:.4f}, {lon:.4f}"
                        except:
                            pass
                    
                    # Cas 2 : Coordonnées UTM
                    if point is None and has_utm:
                        try:
                            x = float(row[colonne_x]) if pd.notna(row[colonne_x]) else None
                            y = float(row[colonne_y]) if pd.notna(row[colonne_y]) else None
                            if x is not None and y is not None:
                                lat, lon = convert_utm_to_latlon(x, y, zone_utm)
                                if lat and lon:
                                    point = Point(lon, lat)
                                    geocode_info = f"UTM → Lat/Lon: {lat:.4f}, {lon:.4f}"
                        except:
                            pass
                    
                    # Cas 3 : Géocodage par nom
                    if point is None and has_lieu:
                        lieu = str(row[colonne_lieu]) if pd.notna(row[colonne_lieu]) else ""
                        if lieu and lieu.strip():
                            status_text.text(f"Géocodage de: {lieu} ({index+1}/{total_rows})")
                            lat, lon = geocode_location(lieu.strip())
                            if lat and lon:
                                point = Point(lon, lat)
                                geocode_info = f"Géocodé: {lieu} → {lat:.4f}, {lon:.4f}"
                            else:
                                geocode_info = f"⚠️ Échec pour: {lieu}"
                    
                    geometries.append(point)
                    geocode_results.append(geocode_info)
                    
                    # Mise à jour de la progression
                    processed += 1
                    progress = 10 + int(80 * (processed / total_rows))
                    progress_bar.progress(progress, f"Traitement {processed}/{total_rows}...")
                
                # Ajout des résultats
                df_geo['geometry'] = geometries
                df_geo['geocode_status'] = geocode_results
                
                # Création du GeoDataFrame
                progress_bar.progress(95, "Création du fichier géospatial...")
                gdf = gpd.GeoDataFrame(df_geo, geometry='geometry', crs="EPSG:4326")
                
                # Filtrer les lignes sans géométrie
                gdf_valid = gdf[gdf.geometry.notna()].copy()
                gdf_invalid = gdf[gdf.geometry.isna()].copy()
                
                progress_bar.progress(100, "✅ Traitement terminé !")
                status_text.empty()
                
                # Affichage des résultats
                st.success(f"✅ Géocodage terminé !")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Localités géocodées", len(gdf_valid))
                with col2:
                    st.metric("❌ Échecs", len(gdf_invalid))
                with col3:
                    st.metric("📊 Total traité", total_rows)
                
                # Afficher les échecs si présents
                if len(gdf_invalid) > 0:
                    with st.expander(f"⚠️ Voir les {len(gdf_invalid)} localités non géocodées"):
                        st.dataframe(gdf_invalid[['geocode_status']].head(20))
                
                # Export
                st.subheader("💾 Téléchargement")
                
                # Préparation du fichier d'export
                export_filename = f"zones_geocodees_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                
                if format_export == "GeoJSON":
                    # Export GeoJSON
                    geojson_str = gdf_valid.to_json()
                    st.download_button(
                        label="📥 Télécharger en GeoJSON",
                        data=geojson_str,
                        file_name=f"{export_filename}.geojson",
                        mime="application/json",
                        use_container_width=True
                    )
                    
                elif format_export == "Shapefile":
                    # Export Shapefile (nécessite un dossier)
                    with tempfile.TemporaryDirectory() as tmpdir:
                        shapefile_path = os.path.join(tmpdir, f"{export_filename}.shp")
                        gdf_valid.to_file(shapefile_path, driver='ESRI Shapefile')
                        
                        # Créer un zip avec tous les fichiers du shapefile
                        import zipfile
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file in os.listdir(tmpdir):
                                file_path = os.path.join(tmpdir, file)
                                zip_file.write(file_path, arcname=file)
                        
                        st.download_button(
                            label="📥 Télécharger en Shapefile (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{export_filename}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                
                elif format_export == "KML":
                    # Export KML
                    kml_str = gdf_valid.to_kml()
                    st.download_button(
                        label="📥 Télécharger en KML",
                        data=kml_str,
                        file_name=f"{export_filename}.kml",
                        mime="application/vnd.google-earth.kml+xml",
                        use_container_width=True
                    )
                
                # Export des données brutes avec coordonnées
                if len(gdf_valid) > 0:
                    # Préparer un DataFrame avec les coordonnées explicites
                    df_export = gdf_valid.copy()
                    df_export['latitude'] = df_export.geometry.y
                    df_export['longitude'] = df_export.geometry.x
                    df_export = df_export.drop(columns=['geometry'])
                    
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger les données brutes (CSV)",
                        data=csv,
                        file_name=f"{export_filename}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                # Aide pour la suite
                st.info("💡 **Prochaine étape** : Importez ce fichier dans QGIS ou un autre SIG pour le superposer avec les données du SIGFU (lotissements et permis miniers).")

# Point d'entrée
if __name__ == "__main__":
    main()
```

---

## 📋 Installation et exécution

### 1. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv_geocodeur
source venv_geocodeur/bin/activate  # Sur Mac/Linux
# ou
venv_geocodeur\Scripts\activate  # Sur Windows
```

### 2. Installer les dépendances

Crée un fichier `requirements.txt` :

```txt
streamlit==1.28.0
pandas==2.1.0
geopandas==0.14.0
geopy==2.3.0
pyproj==3.6.0
shapely==2.0.1
tabula-py==2.9.0
openpyxl==3.1.2
fiona==1.9.4
```

Puis installe :

```bash
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans ton navigateur sur `http://localhost:8501`.

---

## ✨ Fonctionnalités incluses

| Fonctionnalité | Description |
|----------------|-------------|
| **Upload multi-format** | Excel (.xlsx, .xls) et PDF (avec tableaux) |
| **Détection automatique** | L'outil propose les colonnes par défaut en cherchant des mots-clés |
| **Mapping interactif** | L'utilisateur peut sélectionner les colonnes via des dropdowns |
| **3 méthodes de localisation** | Lat/Long, UTM, ou géocodage par nom |
| **Barre de progression** | Suivi en temps réel du traitement |
| **Gestion des erreurs** | Liste des localités non géocodées |
| **Multi-export** | GeoJSON, Shapefile (ZIP), KML, et CSV |
| **Cache intégré** | Évite de re-géocoder deux fois le même lieu |

---

## 🔧 Ce que tu peux améliorer ensuite

1. **Ajouter une base de données locale** des localités ivoiriennes pour réduire les appels API
2. **Support de plus de formats** (CSV, JSON, etc.)
3. **Visualisation sur carte** directement dans l'app (avec `folium` ou `pydeck`)
4. **Mode batch** pour traiter plusieurs fichiers à la fois
5. **Authentification** pour sécuriser l'accès

---

## 🎯 Résumé pour ton ami

> Tu lui donnes cette application. Il :
> 1. Lance `streamlit run app.py`
> 2. Upload son fichier Excel ou PDF
> 3. Sélectionne les bonnes colonnes
> 4. Clique sur "Lancer le géocodage"
> 5. Télécharge son fichier prêt pour QGIS
