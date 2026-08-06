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
            Analizza l'immagine e la descrizione fornita in modo **estremamente sintetico, schematico e a mappa concettuale (solo elenchi puntati brevi e diretti)**.
            
            Dati di contesto:
            - Categoria: {categoria}
            - Numero Giocatori: {num_giocatori}
            - Staff Presente: {num_staff}
            - Durata Seduta: {durata} min
            - Obiettivo Principale: {obiettivi}
            - Descrizione fornita: {descrizione_esercizio}
            - Tipo di contenuto: {tipo_caricamento}
            - Fase della seduta: {fase_seduta}

            Struttura la tua risposta usando RIGOROSAMENTE questo schema sintetico:

            📌 **1. VALUTAZIONE & PUNTEGGI (1-10)**
            * **Adeguatezza Categoria:** [Voto/10] - [Motivazione in 1 riga]
            * **Coerenza Obiettivo:** [Voto/10] - [Motivazione in 1 riga]
            * **Gestione Spazi/Tempi:** [Voto/10] - [Motivazione in 1 riga]
            * 🏆 **PUNTEGGIO GLOBALE:** [Voto Finale/10]

            📊 **2. MAPPA SINTETICA DELL'ESERCIZIO**
            * **Punti di Forza:**
              - ...
              - ...
            * **Criticità / Tempi Morti:**
              - ...
              - ...

            ❓ **3. ANALISI CRITICA: PERCHÉ NON PROPORLA COSÌ?**
            * **Motivi per CUI EVITARE questa configurazione esatta:**
              - ... (es. perché non usare questi spazi, questi vincoli o questo numero di tocchi)
            * **Riflessione Metodologica:**
              - *Cosa succede se si sbaglia la variante?* ...
              - *Perché è meglio una scelta alternativa?* ...

            💡 **4. VARIANTI FLASH**
            * **Correzione di campo immediata:** ...
            * **Variante Semplificazione:** ...
            * **Variante Difficoltà Aumentata:** ...
            """

            with st.spinner("Analisi in corso..."):
                models_to_try = [
                    "openrouter/free",
                    "nvidia/nemotron-nano-12b-v2-vl:free"
                ]

                response = None
                last_exception = None

                for model_name in models_to_try:
                    try:
                        response = client.chat.completions.create(
                            model=model_name,
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
                        if response and response.choices:
                            break
                    except Exception as e:
                        last_exception = e
                        continue

                if response is None:
                    raise last_exception
                
            st.success("Analisi completata!")
            st.markdown("### 📊 Esito Analisi e Valutazione Metodologica")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")
