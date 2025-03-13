import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime

# 🔄 URL d'export CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

# Fonction pour charger les données depuis Google Sheets

def load_data():
    return pd.read_csv(CSV_URL)

data = load_data()

# 🎨 Interface principale
st.title("🏓 Suivi des matchs de Ping-Pong")

# 🎯 📊 Statistiques des victoires avec un camembert
wins = data["Vainqueur"].value_counts()

# 📝 📅 Formulaire d'ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    date = st.date_input("Date", datetime.today())
    player1 = st.text_input("Joueur 1")
    player2 = st.text_input("Joueur 2")
    sets = st.number_input("Nombre de sets gagnant", min_value=1, step=1)
    
    st.markdown("### Scores des Sets")
    set_scores = []
    
    for i in range(sets * 2 - 1):  # Nombre total de sets possibles
        col1, col2 = st.columns(2)
        with col1:
            p1_score = st.number_input(f"Set {i+1} - {player1}", min_value=0, step=1)
        with col2:
            p2_score = st.number_input(f"Set {i+1} - {player2}", min_value=0, step=1)
        set_scores.append((p1_score, p2_score))

    # Calcul automatique du gagnant
    p1_sets_won = sum(1 for s1, s2 in set_scores if s1 > s2)
    p2_sets_won = sum(1 for s1, s2 in set_scores if s2 > s1)

    winner = player1 if p1_sets_won > p2_sets_won else player2
    result = f"{p1_sets_won}-{p2_sets_won}"

    remarks = st.text_area("Remarques")

    submit = st.form_submit_button("Ajouter le match")

    if submit:
        new_match = [str(date), player1, player2] + [s1 for s1, s2 in set_scores] + [p1_sets_won] + [p2_sets_won] + [winner, result, remarks]
        st.success(f"Match ajouté ! {winner} a gagné {result}")

# 🎭 📜 Affichage du tableau des matchs formaté
st.subheader("Historique des matchs")

def format_match_data(df):
    matches = []
    
    for i in range(0, len(df), 2):  # Lire les données en duo (Joueur 1 & Joueur 2)
        row = df.iloc[i]
        opponent_row = df.iloc[i + 1] if i + 1 < len(df) else None  # Vérifier s'il y a un adversaire

        match_date = row["Date"]
        player1 = row["Joueur"]
        player1_scores = row.iloc[2:-1].values  # Récupérer les scores du joueur 1
        player1_sets = row["Total"]

        if opponent_row is not None:
            player2 = opponent_row["Joueur"]
            player2_scores = opponent_row.iloc[2:-1].values  # Scores du joueur 2
            player2_sets = opponent_row["Total"]
        else:
            player2 = ""
            player2_scores = ["-"] * (len(player1_scores))
            player2_sets = ""

        matches.append([match_date, player1] + list(player1_scores) + [player1_sets])
        matches.append(["", player2] + list(player2_scores) + [player2_sets])

    # Créer un DataFrame pour affichage
    columns = ["Date", "Joueur"] + [f"Set {i+1}" for i in range(len(player1_scores))] + ["Total"]
    return pd.DataFrame(matches, columns=columns)

# Transformer et afficher les données sous la nouvelle mise en page
formatted_data = format_match_data(data)
st.dataframe(formatted_data, hide_index=True)
