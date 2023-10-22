import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt

# ----------------- Side bar ------------------

# Informations personnelles
prenom = "Antoine"
nom = "GOULARD"
telephone = "+33 6 67 29 02 52"
linkedin = "https://www.linkedin.com/in/antoine-goulard-pro"
github = "https://github.com/antoinegoulard"
ecole = "www.efrei.fr"

# Sidebar
st.sidebar.header("Informations Auteur")
st.sidebar.markdown("***")
st.sidebar.markdown(f"Prénom: **{prenom}**")
st.sidebar.markdown(f"Nom: **{nom}**")
st.sidebar.markdown(f"No. de téléphone: **{telephone}**")
st.sidebar.markdown(f"Retrouvez moi sur [LinkedIn]({linkedin})")
st.sidebar.markdown(f"Retrouvez moi sur [GitHub]({github})")
st.sidebar.markdown("***")
st.sidebar.markdown(f"Ecole : [EFREI Paris]({ecole})")
st.sidebar.markdown("M1 - Business Intelligence & Analytics")
st.sidebar.image("assets/logo-efrei-paris_transp.png", width=200)

# ----------------------------------------------

st.title('Avis urgents aux navigateurs en vigueur en eaux françaises métropolitaines')
st.subheader('#datavz2023efrei')
st.write('Antoine GOULARD - M1 Business Intelligence & Analytics - Promo 2025 EFREI Paris Panthéon-Assas')

st.markdown('***')

st.markdown('''
<div style="text-align: justify">
    <p>En mer, il arrive que des événements perturbent la navigation en toute sécurité : <strong>épave, bouée disparue, phare en panne, tirs militaires etc.</strong> L’IMO (International Maritime Organization) et l’IHO (International Hydrographic Organization) imposent aux États signataires de la convention SOLAS (Safety of Life at Sea) de recenser et de diffuser les potentiels dangers à la navigation dans les eaux sous leurs responsabilités. Ces informations sont nommées <strong style="color: red;">navigational warnings</strong> dans les conventions internationales et <strong style="color: red;">« avis urgents aux navigateurs » (abrégé en AVURNAV)</strong> en France. La diffusion de ces AVURNAV en France est assurée en mer par VHF, notamment par les sémaphores, après appel sur <strong>le canal 16</strong> ou sur <strong>la fréquence 2 182 kHz</strong>, NAVTEX ou Inmarsat. Ces avis peuvent également être consultés dans les capitaineries des ports et sur les sites des préfets maritimes.</p>
</div>
''', unsafe_allow_html=True)

st.markdown('***')

# Load data
st.subheader(":linked_paperclips: Dataset Preview :")

# Offline version of dataset :
#df = pd.read_csv("Dataset/avurnavs.csv", sep=",")

# Online version of dataset :
df = pd.read_csv('https://raw.githubusercontent.com/snosan-tools/avurnavs-fichiers/master/avurnavs.csv', sep=',')
# source : https://www.data.gouv.fr/fr/datasets/avis-urgents-aux-navigateurs-en-vigueur-en-eaux-francaises-metropolitaines/#/resources
st.write(df.head())

# ---------------- Cleaning data ----------------

df['date_debut_vigueur'] = pd.to_datetime(df['date_debut_vigueur'], errors='coerce')
df = df.dropna(subset=['date_debut_vigueur'])
df = df[df['date_debut_vigueur'].dt.year >= 2018]

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

# Les coordonnées des frontières de la France métropolitaine (zone maritime approximative)
france_metropolitaine_coords = [
    (2.559329,51.527046), (-7.865223,48.129765), (-2.506331,43.309656),
    (8.301455,40.7958), (9.531609,43.914621)
]

# Création d'un polygone avec ces coordonnées
france_metropolitaine_polygon = Polygon(france_metropolitaine_coords)

valid_avis = []

for index, row in df.iterrows():
    # Point avec les coordonnées de l'avis
    point = Point(row['longitude'], row['latitude'])
    
    # Vérification si le point se trouve à l'intérieur du polygone de la France métropolitaine
    if france_metropolitaine_polygon.contains(point):
        valid_avis.append(row)

# Nouveau DataFrame avec les avis valides
df = pd.DataFrame(valid_avis)


# Réinitialiser les index après la suppression
df.reset_index(drop=True, inplace=True)

# ----------------------------------------------

st.markdown('\n\n')
st.subheader(":round_pushpin: Localisation des AVURNAV en France Métropolitaine :")

import folium
from streamlit_folium import st_folium
from streamlit_folium import folium_static
from folium.plugins import Draw, Fullscreen, HeatMap #ScaleControl

def map_AVURNAV():
    
    markers = []

    # Création d'une carte centrée sur la France
    center = [df.latitude.mean(), df.longitude.mean()]
    m = folium.Map(
    location=center,
    zoom_start=6
    ) 
    Draw(export=True).add_to(m)
    Fullscreen(position='topleft').add_to(m)

    # Ajouter une échelle à la carte
    #ScaleControl().add_to(m)

    df['numero_avurnav'].fillna(False, inplace=True)
    df['numero_avurnav'] = df['numero_avurnav'].astype(str)

    max_signalements_par_prefecture = 30

    # Groupement des données par préfecture maritime
    grouped = df.groupby('region_prefecture_maritime')

    # Parcourir chaque groupe
    for key, group in grouped:
        # Sélection aléatoire jusqu'à 30 signalements de ce groupe
        if len(group) > max_signalements_par_prefecture:
            selected_group = group.sample(max_signalements_par_prefecture)
        else:
            selected_group = group

        # Création des marqueurs pour chaque signalement dans ce groupe
        for index, row in selected_group.iterrows():
            lat = row['latitude']
            lon = row['longitude']
            
            popup_info = {
            "number": row['numero_avurnav'],
            "title": row['titre'],
            "content": row['contenu'],
            "latitude": lat,
            "longitude": lon,
            "valid_from": row['date_debut_vigueur'],
            "valid_until": row['date_fin_vigueur'],
            "premar_region": row['region_prefecture_maritime']
            }

            # Formatage du contenu de la popup avec des balises HTML
            popup_content = f"""
            <div style="font-family: Lato; font-size: 12px; border: 1px solid #ccc; padding: 10px;">
                <strong>{popup_info['title']}</strong><br>
                <em>Numéro : {popup_info['number']}</em><br>
                <hr>
                <p>{popup_info['content']}</p>
                <hr>
                <strong>Valide du:</strong> {popup_info['valid_from']} <strong>au</strong> {popup_info['valid_until'] if not pd.isna(popup_info['valid_until']) else 'inconnu'}<br>
                <em>Région Préfecture Maritime : {popup_info['premar_region']}</em>
            </div>
            """

            iframe = folium.IFrame(html=popup_content, width=500, height=300)
            popup = folium.Popup(iframe, max_width=2650)

            custom_icon = folium.CustomIcon(
                icon_image="assets/location-pin.png",
                icon_size=(32, 32),  # Taille de l'icône (largeur, hauteur)
                icon_anchor=(16, 32),  # Point d'ancrage de l'icône (la pointe inférieure au centre)
            )

            markers.append(folium.Marker(
                location=[lat, lon],
                popup=popup, #folium.Popup(popup_content, parse_html=True)
                icon=custom_icon
            ))

    for marker in markers:
        marker.add_to(m)

    return m

# Affichage de la carte
st_data = folium_static(map_AVURNAV(), width=725)

# ----------------------------------------------

st.markdown('***')

#bar chart qui utilise altair
st.subheader("Nombre d'AVURNAV émis par préfecture maritime")

import altair as alt

def bar_chart(df):
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('region_prefecture_maritime:N', axis=alt.Axis(title='Préfecture Maritime', labelAngle=0), sort='-y'),
        y=alt.Y('count():Q', axis=alt.Axis(title='Nombre d\'AVURNAV')),
        color=alt.Color('region_prefecture_maritime:N', legend=alt.Legend(title='Préfecture Maritime'))
    ).properties(
        width=725,
        height=400
    )
    
    return chart

# Affichage
st.altair_chart(bar_chart(df), use_container_width=True)

# ----------------------------------------------

def plot_avis_par_prefecture(df):
    st.subheader('Répartition en % des avis par préfecture maritime')

    # Comptez le nombre d'avis par région préfecture maritime
    avis_par_region = df['region_prefecture_maritime'].value_counts()

    # Camembert
    fig, ax = plt.subplots()
    ax.pie(avis_par_region, labels=avis_par_region.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    ax.set_xlabel('Région Préfecture Maritime', labelpad=20)
    ax.set_ylabel('Nombre d\'avis', labelpad=20)

    # Affichage
    st.pyplot(fig)

plot_avis_par_prefecture(df)

# ----------------------------------------------

st.markdown('***')

import plotly.express as px

st.subheader('Durée moyenne des avis par année et par préfecture maritime')

def duration_plot(df):
    # Filtrage des données pour exclure les avis sans date de fin
    filtered_df = df.dropna(subset=['date_fin_vigueur'])

    # Conversion des colonnes de dates en objets DateTime
    filtered_df['date_debut_vigueur'] = pd.to_datetime(filtered_df['date_debut_vigueur'])
    filtered_df['date_fin_vigueur'] = pd.to_datetime(filtered_df['date_fin_vigueur'])

    # Calcul de la durée en jours et ajout d'une colonne
    filtered_df['duree_avis_jours'] = (filtered_df['date_fin_vigueur'] - filtered_df['date_debut_vigueur']).dt.days

    # Groupement des données par année et par préfecture maritime
    duration_data = filtered_df.groupby(['region_prefecture_maritime', filtered_df['date_debut_vigueur'].dt.year])['duree_avis_jours'].mean().reset_index()

    # Plot interactif de type ligne temporelle
    fig = px.line(
        duration_data,
        x='date_debut_vigueur',
        y='duree_avis_jours',
        color='region_prefecture_maritime',
        labels={'date_debut_vigueur': 'Année', 'duree_avis_jours': 'Durée moyenne des avis en jours', 'region_prefecture_maritime': 'Préfecture Maritime'},
    )

    return fig

st.plotly_chart(duration_plot(df))

# ----------------------------------------------

st.markdown('***')

def interactive_scatter_plot(df):

    # Création d'un nuage de points interactif
    fig = px.scatter(df, x='date_debut_vigueur', y='date_fin_vigueur',
                     color='region_prefecture_maritime', title='Nuage de Points des Avis Maritimes',
                     labels={'region_prefecture_maritime': 'Préfecture Maritime'},
                     hover_name='numero_avurnav',
                     hover_data=['region_prefecture_maritime', 'date_debut_vigueur', 'date_fin_vigueur'])

    fig.update_layout(xaxis_title='Année de début de validité', yaxis_title='Date de fin de validité')
    fig.update_xaxes(nticks=10)  # Nombre de repères sur l'axe x

    selected_point = st.selectbox("Cliquez sur un point pour voir le contenu de l'avis :", df['numero_avurnav'])
    if selected_point:
        avis_contenu = df.loc[df['numero_avurnav'] == selected_point, 'contenu'].values[0]
        st.subheader('Information sur l\'avis :')
        st.markdown(f'<div style="font-size: 12px;">{avis_contenu}</div>', unsafe_allow_html=True)

    # Affichage de nuage de points
    st.plotly_chart(fig)

interactive_scatter_plot(df)

# ----------------------------------------------

st.markdown('***')

st.subheader("Densité des AVURNAV dans l'espace maritime en France métropolitaine")

def heatmap(df, max_signalements_par_prefecture=30):
    locations = df[['latitude', 'longitude']]
    center = [df.latitude.mean(), df.longitude.mean()]
    
    hm = folium.Map(
        location=center,
        zoom_start=6
    ) 
    
    Draw(export=True).add_to(hm)
    Fullscreen(position='topleft').add_to(hm)

    valid_avis = []

    grouped = df.groupby('region_prefecture_maritime')

    for key, group in grouped:
        if len(group) > max_signalements_par_prefecture:
            selected_group = group.sample(max_signalements_par_prefecture)
        else:
            selected_group = group

        for index, row in selected_group.iterrows():
            lat = row['latitude']
            lon = row['longitude']
            valid_avis.append([lat, lon])

    HeatMap(valid_avis).add_to(hm)
    folium_static(hm)

heatmap(df)
