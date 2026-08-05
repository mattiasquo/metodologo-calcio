import streamlit as st
import base64
from openai import OpenAI

# Configurazione interfaccia
st.set_page_config(page_title="Metodologo Virtuale Calcio", layout="centered")
st.title("⚽ Metodologo Virtuale")
st.write("Inserisci i dati della seduta, descrivi l'esercizio e carica l'immagine per ottenere l'analisi e la valutazione.")

# Leggi la chiave da Streamlit Secrets
api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("Inserisci OPENROUTER_API_KEY nei Secrets di Streamlit Cloud.")
    st.stop()

# Inizializza il client OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Form dati allenamento
with st.form("form_allenamento"):
    st.subheader("📋 Dati della Seduta")
    categoria = st.selectbox(
        "Categoria Target",
        ["U8-U9", "U10-U11", "U12-U13", "U14-U15", "U16-U17", "U19/Prima Squadra"]
    )
    num_giocatori = st.number_input("Numero Giocatori Totali", min_value=1, max_value=40, value=14)
    num_staff = st.number_input("Numero Collaboratori/Staff presenti", min_value=1, max_value=10, value=1)
    durata = st.number_input("Durata Totale Seduta (minuti)", min_value=15, max_value=180, value=90)
    obiettivi = st.text_input("Obiettivo/i dell'Allenamento", "Es. Trasmissione e ricerca del terzo uomo")
    
    descrizione_esercizio = st.text_area(
        "Spiegazione / Descrizione dell'Esercitazione", 
        placeholder="Descrivi qui le regole, lo svolgimento, le dimensioni del campo, i vincoli e le varianti...",
        height=150
    )
    
    tipo_caricamento = st.radio("Cosa stai caricando?", ["Esercitazione Singola", "Seduta Completa"])
    fase_seduta = st.selectbox("In quale fase della seduta proponi questo esercizio?", ["Attivazione", "Fase Centrale", "Partita Finale/Situazionale", "Tutta la seduta"])

    uploaded_file = st.file_uploader("Carica l'immagine dell'esercitazione (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
    
    submit_button = st.form_submit_button("Analizza Esercitazione")

if submit_button:
    if uploaded_file is None:
        st.warning("Per favore, carica un'immagine prima di procedere.")
    else:
        try:
            st.image(uploaded_file, caption="Esercitazione Caricata", use_container_width=True)
            
            # Converti l'immagine caricata in base64
            bytes_data = uploaded_file.getvalue()
            base64_image = base64.b64encode(bytes_data).decode('utf-8')
            mime_type = uploaded_file.type

            prompt = f"""
            Sei un esperto metodologo di calcio di livello professionistico. 
            Analizza l'immagine e la spiegazione dell'esercitazione fornita tenendo conto dei seguenti dati:
            
            - Categoria: {categoria}
            - Numero Giocatori: {num_giocatori}
            - Staff Presente: {num_staff}
            - Durata Seduta: {durata} min
            - Obiettivo Principale: {obiettivi}
            - Descrizione/Spiegazione fornita: {descrizione_esercizio}
            - Tipo di contenuto: {tipo_caricamento}
            - Fase della seduta: {fase_seduta}

            Struttura la tua risposta in questo modo preciso:

            1. **VALUTAZIONE E PUNTEGGIO (da 1 a 10):**
               - **Adeguatezza alla Categoria:** [Voto/10 e motivazione breve]
               - **Coerenza con l'Obiettivo:** [Voto/10 e motivazione breve]
               - **Gestione dei Tempi e degli Spazi:** [Voto/10 e motivazione breve]
               - **PUNTEGGIO GLOBALE ESERCITAZIONE:** [Voto Finale/10]

            2. **ANALISI METODOLOGICA DETTAGLIATA:**
               - Punti di forza dell'esercizio
               - Criticità o potenziali tempi morti/rischi

            3. **CONSIGLI E VARIANTI:**
               - Correzioni da fare in campo
               - 2 varianti (una per semplificare, una per aumentare la difficoltà)
            """

            with st.spinner("Analisi e valutazione in corso..."):
                # Nomi esatti ed aggiornati dei modelli Vision gratuiti
                models_to_try = [
                    "google/gemini-2.0-flash-lite-001:free",
                    "qwen/qwen2.5-vl-72b-instruct:free",
                    "openrouter/auto"
                ]

                response = None
                errors_log = []

                for model_name in models_to_try:
                    try:
                        response = client.chat.completions.create(
                            model=model_name,
                            max_tokens=1500,  # Fissa il limite token evitando l'errore 402 sui crediti
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{mime_type};base64,{base64_image}"
                                            },
                                        },
                                    ],
                                }
                            ],
                        )
                        if response and response.choices and len(response.choices) > 0:
                            break
                    except Exception as err:
                        errors_log.append(f"{model_name}: {str(err)}")
                        continue

                if response is None or not response.choices:
                    raise RuntimeError(f"Nessun modello disponibile al momento. Dettagli: {'; '.join(errors_log)}")
                
            st.success("Analisi completata!")
            st.markdown("### 📊 Esito Analisi e Valutazione Metodologica")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")
