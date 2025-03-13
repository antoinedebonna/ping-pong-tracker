import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔄 URL d'export CSV de Google Sheets (si tu veux une autre méthode, sinon utilise gspread)
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

# Charger les données depuis Google Sheets (si tu veux utiliser gspread au lieu de l'URL CSV)
@st.cache_data
def load_data():
    return pd.read_csv(CSV_URL)

data = load_data()

# 🔄 Authentification avec Google Sheets via gspread (si tu préfères utiliser gspread)
def authenticate_gspread():
    # Utilise les secrets de Streamlit (ou credentials.json dans ton cas)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GOOGLE_SHEET_CREDENTIALS"], 
                                                                  ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(CSV_URL)  # Utilise l'URL de ton Google Sheet
    worksheet = sheet.get_worksheet(0)  # Sélectionner la première feuille
    return worksheet

worksheet = authenticate_gspread()

# 🏆 Interface principale
st.title("Suivi des matchs de Ping-Pong")

# 📊 Affichage des stats
wins = data["Vainqueur"].value_counts()
antoine_wins = wins.get("Antoine", 0)
clement_wins = wins.get("Clément", 0)

st.metric(label="Victoires d'Antoine", value=antoine_wins)
st.metric(label="Victoires de Clément", value=clement_wins)

# 📅 Ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    date = st.date_input("Date", datetime.today())
    winner = st.selectbox("Vainqueur", ["Antoine", "Clément"])
    terrain = st.text_input("Terrain")
    sets = st.number_input("Nombre de sets gagnant", min_value=1, step=1)
    result = st.text_input("Résultat (ex: 3-2)")
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")

    if submit:
        new_match = [str(date), winner, terrain, sets, result, remarks]
        worksheet.append_row(new_match)  # 🔄 Ajout à la Google Sheet
        st.success("Match ajouté ! Recharge la page pour voir la mise à jour.")

# 📜 Affichage des matchs
st.subheader("Historique des matchs")
st.dataframe(data)
