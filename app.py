import streamlit as st
import pandas as pd
from datetime import datetime

# Load data (or initialize an empty DataFrame)
@st.cache_data
def load_data():
    return pd.DataFrame(columns=["Date", "Vainqueur", "Terrain", "Nb de sets gagnant", "Résultat", "Remarques"])

data = load_data()

# Title
st.title("Suivi des matchs de Ping-Pong")

# Sidebar filters
st.sidebar.header("Filtres")
selected_year = st.sidebar.selectbox("Année", ["Toutes"] + sorted(set(pd.to_datetime(data["Date"]).dt.year.dropna()), reverse=True))
selected_month = st.sidebar.selectbox("Mois", ["Tous"] + list(range(1, 13)))
selected_terrain = st.sidebar.selectbox("Terrain", ["Tous"] + list(data["Terrain"].unique()))

# Apply filters
filtered_data = data.copy()
if selected_year != "Toutes":
    filtered_data = filtered_data[pd.to_datetime(filtered_data["Date"]).dt.year == selected_year]
if selected_month != "Tous":
    filtered_data = filtered_data[pd.to_datetime(filtered_data["Date"]).dt.month == selected_month]
if selected_terrain != "Tous":
    filtered_data = filtered_data[filtered_data["Terrain"] == selected_terrain]

# Win count
wins = filtered_data["Vainqueur"].value_counts()
antoine_wins = wins.get("Antoine", 0)
clement_wins = wins.get("Clément", 0)

st.metric(label="Victoires d'Antoine", value=antoine_wins)
st.metric(label="Victoires de Clément", value=clement_wins)

# Match history
st.subheader("Historique des matchs")
st.dataframe(filtered_data)

# Add new match
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
        new_match = pd.DataFrame([[date, winner, terrain, sets, result, remarks]], columns=data.columns)
        data = pd.concat([data, new_match], ignore_index=True)
        st.success("Match ajouté ! Recharge la page pour voir la mise à jour.")
