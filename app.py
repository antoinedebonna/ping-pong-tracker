import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# URL de Google Sheets pour chargement des données
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

def load_data():
    return pd.read_csv(CSV_URL)

data = load_data()

# Authentification avec Google Sheets via gspread
def authenticate_gspread():
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["GOOGLE_SHEET_CREDENTIALS"],
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI")
    worksheet = sheet.get_worksheet(0)
    return worksheet

worksheet = authenticate_gspread()

# 🏆 Interface principale
st.title("Suivi des matchs de Ping-Pong")

# 📜 Affichage des matchs sous forme de tableau
st.subheader("Historique des matchs")

# Restructurer les données pour correspondre à l'affichage souhaité
def process_data(data):
    matches = []
    for i in range(0, len(data), 2):  # Deux lignes par match (un joueur par ligne)
        row1 = data.iloc[i]
        row2 = data.iloc[i + 1]
        
        match = {
            "Date": row1["Date"],
            "Terrain": row1["Terrain"],
            "Joueur 1": row1[""],
            "S1": row1["Set 1"], "S2": row1["Set 2"], "S3": row1["Set 3"],
            "S4": row1["Set 4"], "S5": row1["Set 5"],
            "Total": sum([row1[f"Set {i}"] for i in range(1, 6) if pd.notna(row1[f"Set {i}"])]),
            "Joueur 2": row2[""],
            "S1_2": row2["Set 1"], "S2_2": row2["Set 2"], "S3_2": row2["Set 3"],
            "S4_2": row2["Set 4"], "S5_2": row2["Set 5"],
            "Total_2": sum([row2[f"Set {i}"] for i in range(1, 6) if pd.notna(row2[f"Set {i}"])]),
            "Résultat": "✅" if row1["Résultat"] else ""
        }
        matches.append(match)
    return pd.DataFrame(matches)

df_display = process_data(data)

def highlight_winner(val):
    return "font-weight: bold" if val == "✅" else ""

styled_df = df_display.style.applymap(highlight_winner, subset=["Résultat"])
st.dataframe(styled_df)

# 📅 Ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    date = st.date_input("Date", datetime.today())
    terrain = st.text_input("Terrain")
    joueur1 = st.text_input("Joueur 1")
    joueur2 = st.text_input("Joueur 2")
    sets = st.number_input("Nombre de sets gagnant", min_value=1, max_value=5, step=1)
    scores_j1 = [st.number_input(f"Set {i+1} - {joueur1}", min_value=0, step=1) for i in range(sets)]
    scores_j2 = [st.number_input(f"Set {i+1} - {joueur2}", min_value=0, step=1) for i in range(sets)]
    resultat = "✅" if sum(s > s2 for s, s2 in zip(scores_j1, scores_j2)) > sets // 2 else ""
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")

    if submit:
        match_data = [str(date), terrain, joueur1] + scores_j1 + ["", remarks]
        match_data2 = ["", "", joueur2] + scores_j2 + [resultat, ""]
        worksheet.append_row(match_data)
        worksheet.append_row(match_data2)
        st.success("Match ajouté !")
        st.rerun()  # 🔄 Rafraîchit automatiquement la page
