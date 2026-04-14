import streamlit as st
import requests

API_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="Redis AI Search", layout="centered")

st.title("Chatbot Redis Vector DB")

# Input utilisateur
query = st.text_input("Pose ta question :")

if st.button("Envoyer") and query:
    with st.spinner("Recherche en cours..."):
        response = requests.get(API_URL, params={"query": query})
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
        else:
            print("Erreur backend :", response.text)

    st.subheader("Contexte trouvé")
    for c in data["contexts"]:
        st.write("- " + c)

    st.subheader("Réponse")
    st.write(data["answer"])