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

# Ajout de la colonne Résultat
data["Résultat"] = data.apply(lambda row: "✅ V" if row["Total"] == data[data["Date"] == row["Date"]]["Total"].max() else "❌ D", axis=1)

# Statistiques avec camembert (nombre de victoires)
win_counts = data[data["Résultat"] == "✅ V"].groupby("Joueur")["Résultat"].count()
fig = px.pie(win_counts, values=win_counts.values, names=win_counts.index, title="Nombre de victoires par joueur")
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
        
        row_data = [str(date), terrain, "Antoine"] + [s[0] for s in set_scores] + [score_antoine, result_antoine, remarks]
        worksheet.append_row(row_data)
        row_data = ["", terrain, "Clément"] + [s[1] for s in set_scores] + [score_clement, result_clement, ""]
        worksheet.append_row(row_data)
        st.success("Match ajouté !")

# Affichage des matchs formaté avec la colonne "Terrain" et "Résultat"
st.subheader("Historique des matchs")
st.dataframe(data[["Date", "Terrain", "Joueur", "Résultat", "Set 1", "Set 2", "Set 3", "Set 4", "Set 5", "Total", "Remarques"]])
