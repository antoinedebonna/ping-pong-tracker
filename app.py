import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import base64

# URL d'export CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

def load_data():
    return pd.read_csv(CSV_URL)

data = load_data()

def authenticate_gspread():
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["GOOGLE_SHEET_CREDENTIALS"],
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(CSV_URL)
    worksheet = sheet.get_worksheet(0)
    return worksheet

worksheet = authenticate_gspread()

# Interface principale
st.title("Suivi des matchs de Ping-Pong")

# Filtres pour le camembert
st.subheader("Filtres")
data["Date"] = data["Date"].astype(str)  # Assurer que toutes les valeurs sont des chaînes
selected_year = st.selectbox("Sélectionnez une année", sorted(data["Date"].str[:4].dropna().unique(), reverse=True))

selected_terrain = st.selectbox("Sélectionnez un terrain", data["Terrain"].unique())

filtered_data = data[(data["Date"].str.startswith(selected_year)) & (data["Terrain"] == selected_terrain)]

# Statistiques avec camembert (nombre de victoires)
win_counts = filtered_data[filtered_data["Résultat"] == "✅ V"].groupby("Joueur")["Résultat"].count()
fig = px.pie(win_counts, values=win_counts.values, names=win_counts.index, title="Nombre de victoires par joueur", hole=0.3)

# Affichage du nombre de victoires par joueur
for joueur, victoires in win_counts.items():
    st.markdown(f"<h2 style='text-align: center; color: green;'>{joueur}: {victoires} victoires</h2>", unsafe_allow_html=True)

st.plotly_chart(fig)

# Formulaire d'ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    st.markdown("### Antoine vs Clément")
    date = st.date_input("Date", datetime.today())
    terrain = st.text_input("Terrain")
    set_scores = []
    
    for i in range(5):  # Toujours afficher 5 sets
        col1, col2 = st.columns(2)
        with col1:
            score1 = st.number_input(f"Set {i+1} - Antoine", min_value=0, step=1, key=f"score1_{i}")
        with col2:
            score2 = st.number_input(f"Set {i+1} - Clément", min_value=0, step=1, key=f"score2_{i}")
        set_scores.append((score1, score2))
    
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")
    
    if submit:
        score_antoine = sum(1 for s in set_scores if s[0] > s[1])
        score_clement = sum(1 for s in set_scores if s[1] > s[0])
        
        result_antoine = "✅ V" if score_antoine > score_clement else "❌ D"
        result_clement = "✅ V" if score_clement > score_antoine else "❌ D"
        
        row_data = [str(date), terrain, "Antoine", result_antoine] + [s[0] for s in set_scores] + [score_antoine, remarks]
        worksheet.append_row(row_data)
        row_data = ["", terrain, "Clément", result_clement] + [s[1] for s in set_scores] + [score_clement, ""]
        worksheet.append_row(row_data)
        st.success("Match ajouté !")

# Affichage des matchs formaté avec la colonne "Terrain" et "Résultat"
st.subheader("Historique des matchs")
st.dataframe(data[["Date", "Terrain", "Joueur", "Résultat", "Set 1", "Set 2", "Set 3", "Set 4", "Set 5", "Total", "Remarques"]])

# Suppression d'un match
st.subheader("Supprimer un match")
dates = data["Date"].unique()
selected_date = st.selectbox("Sélectionnez la date du match à supprimer", dates)
selected_joueur = st.selectbox("Sélectionnez le joueur", data[data["Date"] == selected_date]["Joueur"].unique())

if st.button("Supprimer"):
    all_records = worksheet.get_all_records()
    new_records = [record for record in all_records if not (record["Date"] == selected_date and record["Joueur"] == selected_joueur)]
    worksheet.clear()
    worksheet.append_row(list(all_records[0].keys()))  # Réécrire les en-têtes
    for record in new_records:
        worksheet.append_row(list(record.values()))
    st.success("Match supprimé !")
