import base64
from groq import Groq
import streamlit as st

# Configurazione interfaccia
st.set_page_config(page_title="Metodologo Virtuale Calcio", layout="centered")
st.title("⚽ Metodologo Virtuale")
st.write(
    "Inserisci i dati della seduta e carica l'immagine dell'esercitazione per"
    " ottenere l'analisi."
)

# API Key Groq hardcoded
api_key = st.secrets["GROQ_API_KEY"]



if api_key:
  client = Groq(api_key=api_key)

  # Form dati allenamento
  with st.form("form_allenamento"):
    st.subheader("📋 Dati della Seduta")
    categoria = st.selectbox(
        "Categoria Target",
        [
            "U8-U9",
            "U10-U11",
            "U12-U13",
            "U14-U15",
            "U16-U17",
            "U19/Prima Squadra",
        ],
    )
    giocatori = st.number_input(
        "Numero Giocatori Totali", min_value=2, max_value=30, value=14
    )
    staff = st.number_input(
        "Numero Collaboratori/Staff presenti",
        min_value=1,
        max_value=10,
        value=1,
    )
    durata = st.number_input(
        "Durata Totale Seduta (minuti)", min_value=30, max_value=120, value=90
    )
    obiettivo = st.text_input(
        "Obiettivo/i dell'Allenamento",
        "Es. Trasmissione e ricerca del terzo uomo",
    )

    tipo_caricamento = st.radio(
        "Cosa stai caricando?", ["Esercitazione Singola", "Seduta Completa"]
    )
    fase = ""
    if tipo_caricamento == "Esercitazione Singola":
      fase = st.text_input(
          "In quale fase della seduta proponi questo esercizio?",
          "Es. Fase Centrale",
      )

    foto = st.file_uploader(
        "Carica la foto o lo schema dell'esercizio",
        type=["jpg", "jpeg", "png"],
    )
    note = st.text_area(
        "Note aggiuntive o descrizione dell'esercizio",
        "Descrivi brevemente lo svolgimento...",
    )

    submitted = st.form_submit_button("Analizza Esercitazione 🚀")

  if submitted:
    if not foto:
      st.error("Per favore, carica un'immagine dell'esercizio.")
    else:
      with st.spinner(
          "Il Metodologo Virtuale sta analizzando l'esercitazione..."
      ):
        # Converti foto in base64 per Groq Vision
        bytes_data = foto.getvalue()
        base64_image = base64.b64encode(bytes_data).decode("utf-8")

        system_prompt = f"""
                Sei un Metodologo Virtuale esperto di calcio.
                Dati forniti dall'allenatore:
                - Categoria: {categoria}
                - N° Giocatori: {giocatori} | Staff: {staff}
                - Durata: {durata} min
                - Obiettivo: {obiettivo}
                - Tipo: {tipo_caricamento} ({fase})
                - Descrizione: {note}

                Analizza l'immagine e i dati forniti applicando rigorosamente la matrice di valutazione sugli 8 criteri (Situazionalità, Specificità, Multidirezionalità, Continuità, Variabilità & Vincoli, Densità Spaziale ~100m²/giocatore, Gestione del Tempo, Architettura Seduta) e controlla se sono stati dichiarati Briefing (+1) e Debriefing (+1).
                
                Restituisci l'analisi ESATTAMENTE nel formato Markdown previsto, fornendo lo score finale, i punteggi per ogni criterio, i Pro, i Contro, le Domande Maieutiche (chiedendo del briefing/debriefing se assenti) e i Suggerimenti Pratici (Step-Up e Step-Down).
                """

        # Chiamata al modello Vision di Groq (llama-3.2-11b-vision-preview)
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }],
            model="llama-3.2-11b-vision",



        )

        st.success("Analisi Completata!")
        st.markdown(chat_completion.choices[0].message.content)
