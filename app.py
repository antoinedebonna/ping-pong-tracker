import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 🔑 Authentification avec Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# 🔄 Charger la Google Sheet
SHEET_NAME = "PingPong_Matches"
sheet = client.open(SHEET_NAME).sheet1

# Charger les données dans un DataFrame (sans mise en cache)
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Interface
st.title("Suivi des matchs de Ping-Pong")

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
        st.success("Match ajouté ! Actualisation des données en cours...")

        # 🚀 Forcer la mise à jour en rechargeant les données après ajout
        st.experimental_rerun()

# 📜 Affichage des matchs
st.subheader("Historique des matchs")
data = load_data()  # 🔄 Charger à nouveau les données
st.dataframe(data)
