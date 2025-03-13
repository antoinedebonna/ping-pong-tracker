import streamlit as st
import pandas as pd
from datetime import datetime

# 🐄 URL d'export CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

# Charger les données depuis Google Sheets
@st.cache_data
def load_data():
    return pd.read_csv(CSV_URL)

data = load_data()

# 🎨 Mise en page adaptée
st.title("Suivi des matchs de Ping-Pong 🏳")

# Transformer les données pour correspondre à la mise en page souhaitée

def calculate_set_wins(scores1, scores2):
    player1_sets = 0
    player2_sets = 0
    
    for s1, s2 in zip(scores1, scores2):
        if s1 > s2:
            player1_sets += 1
        elif s2 > s1:
            player2_sets += 1
    
    return player1_sets, player2_sets


def format_match_data(df):
    matches = []
    
    for i in range(0, len(df), 2):  # Lire les données en duo (Joueur 1 & Joueur 2)
        row = df.iloc[i]
        opponent_row = df.iloc[i + 1] if i + 1 < len(df) else None  # Vérifier s'il y a un adversaire

        match_date = row["Date"]
        player1 = row["Joueur"]
        player1_scores = row.iloc[2:-1].astype(int).values  # Récupérer les scores du joueur 1

        if opponent_row is not None:
            player2 = opponent_row["Joueur"]
            player2_scores = opponent_row.iloc[2:-1].astype(int).values  # Scores du joueur 2
        else:
            player2 = ""
            player2_scores = [0] * len(player1_scores)

        # Calculer les sets gagnés
        player1_sets, player2_sets = calculate_set_wins(player1_scores, player2_scores)

        matches.append([match_date, player1] + list(player1_scores) + [player1_sets])
        matches.append(["", player2] + list(player2_scores) + [player2_sets])

    # Créer un DataFrame pour affichage
    columns = ["Date", "Joueur"] + [f"Set {i+1}" for i in range(len(player1_scores))] + ["Total"]
    return pd.DataFrame(matches, columns=columns)

# Transformer et afficher les données sous la nouvelle mise en page
formatted_data = format_match_data(data)
st.dataframe(formatted_data, hide_index=True)
