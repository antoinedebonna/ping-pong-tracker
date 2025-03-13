import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔄 URL d'export CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

# Charger les données depuis Google Sheets
def load_data():
    return pd.read_csv(CSV_URL)

data = load_data()

# 🔄 Authentification avec Google Sheets via gspread
def authenticate_gspread():
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GOOGLE_SHEET_CREDENTIALS"], 
                                                                  ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(CSV_URL)
    worksheet = sheet.get_worksheet(0)
    return worksheet

worksheet = authenticate_gspread()

# 🏆 Interface principale
st.title("Suivi des matchs de Ping-Pong")

# 📊 Affichage des stats
wins = data["Vainqueur"].value_counts()
labels = ["Antoine", "Clément"]
values = [wins.get("Antoine", 0), wins.get("Clément", 0)]

fig, ax = plt.subplots()
ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=["blue", "red"])
ax.axis("equal")  # Assure que le camembert est un cercle
st.pyplot(fig)

# 📅 Ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    date = st.date_input("Date", datetime.today())
    winner = st.selectbox("Vainqueur", ["Antoine", "Clément"])
    terrain = st.text_input("Terrain")
    sets = st.number_input("Nombre de sets gagnant", min_value=1, step=1)
    
    # Champs pour entrer les scores de chaque set
    scores = []
    for i in range(sets * 2 - 1):
        scores.append(st.text_input(f"Score Set {i+1}", ""))
    
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")
    
    if submit:
        result = "-".join(scores)  # Format des résultats en "11-9, 9-11, 11-7"
        new_match = [str(date), winner, terrain, sets, result, remarks]
        worksheet.append_row(new_match)
        st.success("Match ajouté !")
        st.experimental_rerun()  # Recharge la page automatiquement

# 📜 Affichage des matchs
st.subheader("Historique des matchs")
st.dataframe(data)
