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

# Filtres pour le camembert
st.subheader("Filtres")
selected_years = st.multiselect("Sélectionnez une ou plusieurs années", sorted(data["Date"].str[:4].dropna().unique(), reverse=True))
selected_terrains = st.multiselect("Sélectionnez un ou plusieurs terrains", data["Terrain"].dropna().unique())

# Filtrage des données
filtered_data = data[data["Date"].str[:4].isin(selected_years) & data["Terrain"].isin(selected_terrains)]
st.write("Nombre de lignes après filtrage :", len(filtered_data))

# Statistiques avec camembert (nombre de victoires)
if not filtered_data.empty:
    win_counts = filtered_data.groupby(["Joueur", "Résultat"]).size().unstack(fill_value=0)
    
    if not win_counts.empty:
        if "✅ V" in win_counts.columns:
            win_counts = win_counts["✅ V"]  # Ne prendre que les victoires
        else:
            win_counts = pd.Series(0, index=win_counts.index)  # Cas où aucune victoire n'est trouvée
        
        fig = px.pie(win_counts, values=win_counts.values, names=win_counts.index, 
                     title="Nombre de victoires par joueur", hole=0.3)

        st.plotly_chart(fig, key="win_chart")
    else:
        st.warning("Aucune victoire détectée pour ce filtre.")
else:
    st.warning("Aucune donnée trouvée pour les filtres sélectionnés.")

# Graphique en ligne (évolution des victoires)
if not filtered_data.empty:
    if "Date" in filtered_data.columns and not filtered_data["Date"].isnull().all():
        filtered_data = filtered_data.sort_values("Date").reset_index(drop=True)
        filtered_data["Match_Numero"] = range(1, len(filtered_data) + 1)
    else:
        st.warning("Les données n'ont pas de colonne 'Date' valide.")

    
    # Calculer le cumul des victoires
    cumulative_wins = filtered_data.copy()
    cumulative_wins["Victoire_Cumul"] = cumulative_wins.groupby("Joueur")["Résultat"].transform(lambda x: (x == "✅ V").astype(int).cumsum())


    
    fig_line = px.line(cumulative_wins, x="Match_Numero", y="Victoire_Cumul", color="Joueur", markers=True,
                        title="Évolution des victoires par joueur",
                        labels={"Match_Numero": "Numéro du match", "Victoire_Cumul": "Total de victoires cumulées"})
    st.plotly_chart(fig_line, key="win_evolution")

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
        
        row_data = [str(date), terrain, "Antoine", result_antoine] + [s[0] for s in set_scores] + [score_antoine, remarks]
        worksheet.append_row(row_data)
        row_data = ["", terrain, "Clément", result_clement] + [s[1] for s in set_scores] + [score_clement, ""]
        worksheet.append_row(row_data)
        st.success("Match ajouté !")

# Suppression d'un match
st.subheader("Supprimer un match")
dates = data["Date"].unique()
selected_date = st.selectbox("Sélectionnez la date du match à supprimer", dates)
selected_joueur = st.selectbox("Sélectionnez le joueur", data[data["Date"] == selected_date]["Joueur"].unique())

if st.button("Supprimer"):
    all_values = worksheet.get_all_values()
    headers = all_values[0]
    rows = all_values[1:]
    
    index_to_delete = None
    for i, row in enumerate(rows, start=2):  # Start at 2 to match Google Sheets row numbers
        if row[0] == selected_date and row[2] == selected_joueur:  # Colonne Date et Joueur
            index_to_delete = i
            break
    
    if index_to_delete:
        worksheet.delete_rows(index_to_delete)
        st.success("Match supprimé !")
    else:
        st.warning("Match non trouvé.")
