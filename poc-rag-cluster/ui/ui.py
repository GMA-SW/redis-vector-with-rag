# ================================
# IMPORTS
# ================================
import streamlit as st
import requests


# ================================
# CONFIGURATION
# ================================
API_URL = "http://localhost:8000/ask"

st.set_page_config(
    page_title="Redis AI Search",
    layout="centered"
)


# ================================
# UI
# ================================
st.title("Chatbot Redis Vector DB")

query = st.text_input("Pose ta question :")


# ================================
# BACKEND CALL
# ================================
def call_api(query):
    response = requests.get(API_URL, params={"query": query})

    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()

    print("Erreur backend :", response.text)
    return None


# ================================
# DISPLAY
# ================================
def display_contexts(contexts):
    st.subheader("Contexte trouvé")
    for c in contexts:
        st.write("- " + c)


def display_answer(answer):
    st.subheader("Réponse")
    st.write(answer)


# ================================
# MAIN FLOW
# ================================
if st.button("Envoyer") and query:
    with st.spinner("Recherche en cours..."):
        data = call_api(query)

    if data:
        display_contexts(data["contexts"])
        display_answer(data["answer"])