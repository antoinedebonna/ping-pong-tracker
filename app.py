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

# 📊 Affichage des statistiques sous forme de camembert
wins = data["Vainqueur"].value_counts()
fig, ax = plt.subplots()
ax.pie(wins, labels=wins.index, autopct='%1.1f%%', colors=["#FF9999", "#66B2FF"])
st.pyplot(fig)

# 📅 Ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    date = st.date_input("Date", datetime.today())
    player1 = st.text_input("Joueur 1")
    player2 = st.text_input("Joueur 2")
    sets = st.number_input("Nombre de sets gagnants", min_value=1, max_value=4, step=1)
    
    scores = []
    for i in range(sets * 2 - 1):  # Nombre max de sets joués
        col1, col2 = st.columns(2)
        with col1:
            score1 = st.number_input(f"Set {i+1} - {player1}", min_value=0, step=1)
        with col2:
            score2 = st.number_input(f"Set {i+1} - {player2}", min_value=0, step=1)
        scores.append((score1, score2))
    
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")

    if submit:
        # Calcul du vainqueur
        sets_won_p1 = sum(1 for s1, s2 in scores if s1 > s2)
        sets_won_p2 = sum(1 for s1, s2 in scores if s2 > s1)
        
        if sets_won_p1 > sets_won_p2:
            winner = player1
        else:
            winner = player2
        
        # Format des scores pour enregistrement
        formatted_scores = [s for pair in scores for s in pair]
        new_match = [str(date), player1, player2] + formatted_scores + [sets_won_p1, sets_won_p2, winner, remarks]
        
        # Ajouter à Google Sheets
        worksheet.append_row(new_match)
        
        st.success("Match ajouté !")
        st.experimental_rerun()  # 🔄 Rafraîchissement automatique

# 📜 Affichage des matchs sous forme de tableau
st.subheader("Historique des matchs")

# Création du tableau
columns = ["Date", "Joueur", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "Total", "Résultat"]
df = data[columns]

# Mise en gras du vainqueur
def highlight_winner(val):
    return "font-weight: bold" if val == max(df["Total"]) else ""

styled_df = df.style.applymap(highlight_winner, subset=["Total"])

st.dataframe(styled_df)
