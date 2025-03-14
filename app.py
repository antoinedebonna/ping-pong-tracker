import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import base64

# URL d'export CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

def load_data():
    data = pd.read_csv(CSV_URL)
    data["Date"].fillna(method='ffill', inplace=True)  # Remplir les NaN avec la valeur précédente
    data["Date"] = data["Date"].astype(str)
    data["Terrain"] = data["Terrain"].astype(str).fillna("Inconnu")
    return data

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

# Filtres pour les graphiques et le tableau
st.subheader("Filtres")
available_years = sorted(data["Date"].str[:4].dropna().unique(), reverse=True)
available_terrains = data["Terrain"].dropna().unique()

selected_years = st.multiselect("Sélectionnez une ou plusieurs années", available_years, default=available_years)
selected_terrains = st.multiselect("Sélectionnez un ou plusieurs terrains", available_terrains, default=available_terrains)

# Filtrage des données
data_filtered = data[data["Date"].str[:4].isin(selected_years) & data["Terrain"].isin(selected_terrains)]
data_filtered = data_filtered.sort_values(by="Date").reset_index(drop=True)

# Ajouter une colonne "Match #" qui attribue le même numéro aux deux lignes d'un match
data_filtered["Match #"] = (data_filtered.index // 2) + 1

st.write("Nombre de lignes après filtrage :", len(data_filtered))

# Statistiques avec camembert (nombre de victoires)
if not data_filtered.empty:
    win_counts = data_filtered.groupby(["Joueur", "Résultat"]).size().unstack(fill_value=0)
    
    if "✅ V" in win_counts.columns:
        win_counts = win_counts["✅ V"]
    else:
        win_counts = pd.Series(0, index=win_counts.index)
    
    fig_pie = px.pie(win_counts, values=win_counts.values, names=win_counts.index, 
                      title="Nombre de victoires par joueur", hole=0.3)
    st.plotly_chart(fig_pie, key="win_chart")
else:
    st.warning("Aucune donnée trouvée pour les filtres sélectionnés.")

# Graphique d'évolution des victoires
data_victories = data_filtered[data_filtered["Résultat"] == "✅ V"].copy()
data_victories["Cumulative Wins"] = data_victories.groupby("Joueur").cumcount() + 1

if not data_victories.empty:
    fig_line = px.line(data_victories, x="Match #", y="Cumulative Wins", color="Joueur",
                       title="Évolution du nombre de victoires par joueur",
                       markers=True)
    st.plotly_chart(fig_line, key="evolution_victoires")

# Formulaire d'ajout de match
st.subheader("Ajouter un match")
with st.form("add_match_form"):
    st.markdown("### Antoine vs Clément")
    date = st.date_input("Date", datetime.today())
    terrain = st.text_input("Terrain")
    set_scores = []
    
    for i in range(5):  # Toujours afficher 5 sets
        col1, col2 = st.columns(2)
        with col1:
            score1 = st.number_input(f"Set {i+1} - Antoine", min_value=0, step=1, key=f"score1_{i}")
        with col2:
            score2 = st.number_input(f"Set {i+1} - Clément", min_value=0, step=1, key=f"score2_{i}")
        set_scores.append((score1, score2))
    
    remarks = st.text_area("Remarques")
    submit = st.form_submit_button("Ajouter")
    
    if submit:
        score_antoine = sum(1 for s in set_scores if s[0] > s[1])
        score_clement = sum(1 for s in set_scores if s[1] > s[0])
        
        result_antoine = "✅ V" if score_antoine > score_clement else "❌ D"
        result_clement = "✅ V" if score_clement > score_antoine else "❌ D"
        
        worksheet.append_row([str(date), terrain, "Antoine", result_antoine] + [s[0] for s in set_scores] + [score_antoine, remarks])
        worksheet.append_row([str(date), terrain, "Clément", result_clement] + [s[1] for s in set_scores] + [score_clement, ""])
        st.success("Match ajouté !")

st.dataframe(data_filtered)  # Afficher le tableau filtré

# Suppression d'un match
st.subheader("Supprimer un match")
selected_match = st.selectbox("Sélectionnez le numéro du match à supprimer", sorted(data_filtered["Match #"].unique()))

if st.button("Supprimer"):
    all_values = worksheet.get_all_values()
    headers = all_values[0]
    rows = all_values[1:]

    # Trouver les index des lignes correspondant au match sélectionné
    indexes_to_delete = []
    match_number = int(selected_match)

    current_match_number = 1  # Numéro de match en parcourant les lignes
    for i in range(len(rows)):
        if i % 2 == 0:  # On ne compte qu'une ligne sur deux pour identifier les matchs
            if current_match_number == match_number:
                indexes_to_delete.extend([i + 2, i + 3])  # Les lignes de Google Sheets commencent à 1
                break  # On s'arrête dès qu'on a trouvé le match
            current_match_number += 1  # Incrémentation du match

    if indexes_to_delete:
        for i in reversed(indexes_to_delete):  # Supprimer de la fin vers le début
            worksheet.delete_rows(i)
        st.success(f"Match {selected_match} supprimé !")
    else:
        st.warning("Match non trouvé.")

