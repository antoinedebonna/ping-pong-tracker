import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# 🔄 Connexion à Google Sheets avec authentification
gc = gspread.service_account(filename='credentials.json')  # Utilise un fichier JSON d'authentification

SHEET_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/edit?usp=sharing"
sh = gc.open_by_url(SHEET_URL)
worksheet = sh.sheet1

# Charger les données
def load_data():
    data = worksheet.get_all_records()
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
        worksheet.append_row(new_match)  # 🔄 Ajout à la Google Sheet
        st.success("Match ajouté ! Recharge la page pour voir la mise à jour.")

# 📜 Affichage des matchs
st.subheader("Historique des matchs")
st.dataframe(data)
