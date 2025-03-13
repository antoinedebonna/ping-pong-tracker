import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

# Statistiques avec camembert
win_counts = data.groupby("Joueur")["Total"].sum().dropna()
fig = px.pie(win_counts, values=win_counts.values, names=win_counts.index, title="Répartition des victoires")
st.plotly_chart(fig)

# Formulaire d'ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    date = st.date_input("Date", datetime.today())
    terrain = st.text_input("Terrain")
    player1 = st.text_input("Joueur 1")
    player2 = st.text_input("Joueur 2")
    sets = st.number_input("Nombre de sets gagnants", min_value=1, step=1)
    set_scores = []
    
    for i in range(sets * 2 - 1):
        col1, col2 = st.columns(2)
        with col1:
            score1 = st.number_input(f"Set {i+1} - {player1}", min_value=0, step=1, key=f"score1_set{i}")


        with col2:
            score2 = st.number_input(f"Set {i+1} - {player2}", min_value=0, step=1, key=f"score2_set{i}")
        set_scores.append((score1, score2))
    
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")
    
    if submit:
        row_data = [str(date), terrain, player1] + [s[0] for s in set_scores] + [sum(1 for s in set_scores if s[0] > s[1]), remarks]
        worksheet.append_row(row_data)
        row_data = ["", "", player2] + [s[1] for s in set_scores] + [sum(1 for s in set_scores if s[1] > s[0]), ""]
        worksheet.append_row(row_data)
        st.success("Match ajouté ! Recharge la page pour voir la mise à jour.")

# Affichage des matchs formaté
st.subheader("Historique des matchs")
st.dataframe(data)
