import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.markdown(
    """
    <style>
        /* Ajouter un fond d'écran avec une teinte sombre pour améliorer la lisibilité */
        body {
            background-image: url("https://i.pinimg.com/736x/2f/b8/bc/2fb8bca72f5f2433546398fcc83eaa3a.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        /* Ajouter une couche semi-transparente noire sur l'image de fond */
        .stApp {
            background: rgba(0, 0, 0, 0.5); /* 50% noir transparent */
        }

        /* Appliquer un léger flou sur l'image de fond uniquement */
        body {
            filter: blur(5px); /* Applique un flou sur le fond */
            -webkit-filter: blur(5px); /* Pour les navigateurs WebKit */
        }

        /* Supprimer le flou sur le contenu principal (texte, graphiques, etc.) */
        .stApp > div {
            filter: none;
        }

        /* Améliorer la lisibilité du texte */
        .stText, .stMarkdown, .stDataFrame, .stSubheader, .stHeader, .stButton, .stFormLabel, .stSelectbox, .stMultiselect {
            color: #f0f0f0 !important;  /* Couleur claire pour le texte */
        }

        /* Améliorer le contraste du texte dans les widgets */
        .stSelectbox, .stMultiselect, .stTextInput, .stTextArea, .stNumberInput {
            background-color: rgba(255, 255, 255, 0.7); /* Fond blanc semi-transparent pour les champs de saisie */
            color: #333;  /* Couleur du texte des champs de saisie */
        }
    </style>
    """,
    unsafe_allow_html=True
)




# URL d'export CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/1S9mBu7_hSwSb0JQH-jAQNRUlOWQho6HcGoLJ8B0QjaI/export?format=csv"

# Charger les données depuis Google Sheets
def load_data():
    data = pd.read_csv(CSV_URL)
    data["Date"].fillna(method='ffill', inplace=True)
    data["Date"] = data["Date"].astype(str)
    data["Terrain"] = data["Terrain"].astype(str).fillna("Inconnu")
    return data

data = load_data()

# Authentification Google Sheets
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

# Création des onglets
tab1, tab2 = st.tabs(["📊 Statistiques & Tableaux", "⚙️ Gestion des matchs"])

# 🏓 Onglet 1 : Statistiques et Tableau
with tab1:
    st.subheader("Filtres")
    available_years = sorted(data["Date"].str[:4].dropna().unique(), reverse=True)
    available_terrains = data["Terrain"].dropna().unique()

    selected_years = st.multiselect("Sélectionnez une ou plusieurs années", available_years, default=available_years)
    selected_terrains = st.multiselect("Sélectionnez un ou plusieurs terrains", available_terrains, default=available_terrains)

    # Filtrage des données
    data_filtered = data[data["Date"].str[:4].isin(selected_years) & data["Terrain"].isin(selected_terrains)]
    data_filtered = data_filtered.sort_values(by="Date").reset_index(drop=True)
    data_filtered["Match #"] = (data_filtered.index // 2) + 1  # Numérotation des matchs

    st.write(f"Nombre de matchs après filtrage : {len(data_filtered) // 2}")

    # 📊 Graphique des victoires
    if not data_filtered.empty:
        win_counts = data_filtered.groupby(["Joueur", "Résultat"]).size().unstack(fill_value=0)
        win_counts = win_counts.get("✅ V", pd.Series(0, index=win_counts.index))

        fig_pie = px.pie(win_counts, values=win_counts.values, names=win_counts.index, title="Nombre de victoires par joueur", hole=0.3)
        st.plotly_chart(fig_pie)

    # 📈 Graphique d'évolution des victoires
    data_victories = data_filtered[data_filtered["Résultat"] == "✅ V"].copy()
    data_victories["Cumulative Wins"] = data_victories.groupby("Joueur").cumcount() + 1

    if not data_victories.empty:
        fig_line = px.line(data_victories, x="Match #", y="Cumulative Wins", color="Joueur", title="Évolution du nombre de victoires par joueur", markers=True)
        st.plotly_chart(fig_line)

    # 📋 Affichage du tableau des matchs filtrés avec le numéro de match en 1ère colonne

    set_columns = [f"Set {i+1}" for i in range(5)]  # Génération des colonnes de sets
    columns_to_display = ["Match #", "Date", "Terrain", "Joueur", "Résultat"] + set_columns  # Ajout des sets
    
    data_filtered_display = data_filtered[columns_to_display]
    st.dataframe(data_filtered_display.set_index("Match #"))
    st.markdown("""
        <style>
            /* Réduit la largeur des colonnes spécifiques */
            div[data-testid="stDataFrame"] th:nth-child(1),
            div[data-testid="stDataFrame"] td:nth-child(1),
            div[data-testid="stDataFrame"] th:nth-child(6),
            div[data-testid="stDataFrame"] td:nth-child(6),
            div[data-testid="stDataFrame"] th:nth-child(7),
            div[data-testid="stDataFrame"] td:nth-child(7),
            div[data-testid="stDataFrame"] th:nth-child(8),
            div[data-testid="stDataFrame"] td:nth-child(8),
            div[data-testid="stDataFrame"] th:nth-child(9),
            div[data-testid="stDataFrame"] td:nth-child(9),
            div[data-testid="stDataFrame"] th:nth-child(10),
            div[data-testid="stDataFrame"] td:nth-child(10) {
                min-width: 50px !important;  /* Ajuste la largeur minimale */
                max-width: 50px !important;
                text-align: center !important;
            }
        </style>
    """, unsafe_allow_html=True)


    # 🗑️ Suppression d'un match (cachée sous un menu déroulant)
    with st.expander("🗑️ Supprimer un match"):
        selected_match = st.selectbox("Sélectionnez le numéro du match à supprimer", sorted(data_filtered["Match #"].unique()))

        if st.button("Supprimer"):
            all_values = worksheet.get_all_values()
            rows = all_values[1:]

            indexes_to_delete = []
            match_number = int(selected_match)

            current_match_number = 1  # Numéro de match en parcourant les lignes
            for i in range(len(rows)):
                if i % 2 == 0:  # On ne compte qu'une ligne sur deux pour identifier les matchs
                    if current_match_number == match_number:
                        indexes_to_delete.extend([i + 2, i + 3])  # Google Sheets commence à 1
                        break
                    current_match_number += 1

            if indexes_to_delete:
                for i in reversed(indexes_to_delete):  # Supprimer de la fin vers le début
                    worksheet.delete_rows(i)
                st.success(f"Match {selected_match} supprimé !")
            else:
                st.warning("Match non trouvé.")

# ➕ Onglet 2 : Formulaire d'ajout de match
with tab2:
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
