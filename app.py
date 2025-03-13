import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 🔑 Authentification avec Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("chemin/vers/ton/fichier.json", scope)
client = gspread.authorize(creds)

# 🔄 Charger la Google Sheet
SHEET_NAME = "PingPong_Matches"
sheet = client.open(SHEET_NAME).sheet1

# Charger les données dans un DataFrame
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

data = load_data()

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
        sheet.append_row(new_match)  # 🔄 Ajout à la Google Sheet
        st.success("Match ajouté ! Recharge la page pour voir la mise à jour.")

# 📜 Affichage des matchs
st.subheader("Historique des matchs")
st.dataframe(data)
