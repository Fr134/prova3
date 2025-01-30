import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")  # Configura il layout per occupare tutta la larghezza della pagina
#Funzione per leggere il primo file excel
def process_excel_to_dataframe(file_path):
    """
    Legge un file Excel con dati organizzati su più fogli e restituisce un DataFrame consolidato con informazioni
    sul cliente, anno, mese e le prime 5 colonne dei fogli mensili.

    Args:
        file_path (str): Il percorso del file Excel.

    Returns:
        pd.DataFrame: DataFrame consolidato con i dati richiesti.
    """
    try:
        # Legge tutti i fogli del file Excel
        excel_data = pd.read_excel(file_path, sheet_name=None) if isinstance(file_path, str) else file_path

        
        # Recupera il primo foglio per ottenere informazioni sul cliente e sull'anno
        first_sheet = list(excel_data.keys())[0]
        metadata = excel_data[first_sheet]
        metadata.columns = metadata.columns.str.strip()  # Rimuove spazi dai nomi delle colonne
        cliente = metadata.iloc[0, 0]  # Prima colonna, prima riga (Nome cliente)
        
        



        # Corregge l'anno, rimuovendo caratteri non numerici e assicurandosi che sia un intero
        anno = str(metadata.iloc[0, 1]).replace(",", "").strip()  # Rimuove virgole o spazi
        anno = int(float(anno))  # Converte in intero per evitare errori
        
        # Controlla se la colonna dello sconto di secondo livello è disponibile
        if metadata.shape[1] > 2:
            sconto_secondo_livello = float(metadata.iloc[0, 2])
        else:
            sconto_secondo_livello = 0  # Valore predefinito
            
        # Controlla se la colonna dello sconto di primo livello è disponibile   
        if metadata.shape[1] > 3:
            sconto_primo_livello = float(metadata.iloc[0, 3])
        else:
            sconto_primo_livello = 0  # Valore predefinito
        
                



        # Inizializza un DataFrame vuoto per i dati consolidati
        consolidated_data = pd.DataFrame()

        # Itera su tutti i fogli eccetto il primo (che è per i metadati)
        for sheet_name, sheet_data in excel_data.items():
            if sheet_name == first_sheet:
                continue

            # Estrae le prime 5 colonne del foglio
            sheet_data = sheet_data.iloc[:, :5]

            # Converte i valori numerici con virgola come separatore decimale
            numeric_columns = ['Fatturato_Anno_Prec', 'Cartoni_Venduti_Prec', 'Fatturato', 'Cartoni_Venduti']
            for col in numeric_columns:
                if col in sheet_data.columns:
                    sheet_data[col] = pd.to_numeric(sheet_data[col].replace(",", ".", regex=True), errors='coerce')

            # Aggiunge colonne per cliente, anno, mese sconto di primo e secondo livello
            sheet_data['Cliente'] = cliente
            sheet_data['Anno'] = anno
            sheet_data['Mese'] = sheet_name
            sheet_data['Sconto secondo livello'] = sconto_secondo_livello
            sheet_data['Sconto primo livello'] = sconto_primo_livello
            

            # Accoda i dati al DataFrame consolidato
            consolidated_data = pd.concat([consolidated_data, sheet_data], ignore_index=True)
            
        # Specifica la colonna in cui vuoi eliminare le righe con valori nulli
        colonna_target = 'Referente'

        # Elimina le righe con valore nullo nella colonna specificata
        consolidated_data = consolidated_data[consolidated_data[colonna_target].notna()]

        # Trasforma 'Mese' e 'Anno' in 'Data'
        consolidated_data = combine_month_year_to_date(consolidated_data)

        return consolidated_data

    except Exception as e:
        print(f"Errore durante l'elaborazione del file Excel: {e}")
        return pd.DataFrame()


def process_uploaded_files(uploaded_files):
    dataframes = []
    details_dataframe = None

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name.lower()
        df = pd.read_excel(uploaded_file, sheet_name=None)  # Legge tutti i fogli
        
        if filename == "dettagli_referenze.xlsx":
            details_dataframe = process_second_excel_to_dataframe(df)
        else:
            dataframes.append(process_excel_to_dataframe(df))

    return dataframes, details_dataframe



#legge il secondo file excel

def process_second_excel_to_dataframe(file_path):
    """
    Legge un secondo file Excel e restituisce un DataFrame con le prime 5 colonne richieste.

    Args:
        file_path (str): Il percorso del secondo file Excel.

    Returns:
        pd.DataFrame: DataFrame contenente le prime 6 colonne.
    """
    try:
        # Legge il file Excel e seleziona le prime 5 colonne
        second_data = pd.read_excel(file_path, usecols=range(6)) if isinstance(file_path, str) else file_path[list(file_path.keys())[0]].iloc[:, :6]


        # Rinomina le colonne per uniformità
        second_data.columns = ['Referente', 'Nome', 'Quantita in grammi', 'Pezzi in un cartone', 'Ricetta', 'Listino']

        
        return second_data

    except Exception as e:
        print(f"Errore durante l'elaborazione del secondo file Excel: {e}")
        return pd.DataFrame()


    #Funzione per combinare mesi e anni e assegnare a ogni riga la data mm/aa
def combine_month_year_to_date(dataframe):
    """
    Combina le colonne 'Mese' e 'Anno' in una singola colonna datetime 'Data' nel formato mm/aaaa.

    Args:
        dataframe (pd.DataFrame): Il DataFrame con le colonne 'Mese' e 'Anno'.

    Returns:
        pd.DataFrame: Il DataFrame aggiornato con una singola colonna 'Data'.
    """
    try:
        # Traduzione dei mesi dall'italiano all'inglese
        months_translation = {
            "GENNAIO": "January", "FEBBRAIO": "February", "MARZO": "March",
            "APRILE": "April", "MAGGIO": "May", "GIUGNO": "June",
            "LUGLIO": "July", "AGOSTO": "August", "SETTEMBRE": "September",
            "OTTOBRE": "October", "NOVEMBRE": "November", "DICEMBRE": "December"
        }
        dataframe['Mese'] = dataframe['Mese'].map(months_translation)
     
        # Creazione della colonna 'Data' combinando 'Mese' e 'Anno'
        dataframe['Data'] = pd.to_datetime(
            dataframe['Mese'].str.strip() + ' ' + dataframe['Anno'].astype(str),
            format='%B %Y',
            errors='coerce'
        ).dt.strftime('%m/%Y')

        # Verifica se ci sono errori nella conversione
        if dataframe['Data'].isna().any():
            print("Alcuni valori di 'Mese' o 'Anno' non sono stati convertiti correttamente.")

        # Rimuove le colonne 'Mese' e 'Anno'
        dataframe.drop(columns=['Mese', 'Anno'], inplace=True)

        return dataframe

    except Exception as e:
        print(f"Errore durante la conversione delle colonne 'Mese' e 'Anno' in 'Data': {e}")
        return dataframe


#funzione per combinare i due dataframe 
def merge_with_second_dataframe(main_dataframe, second_dataframe):
    """
    Unisce il DataFrame principale con il secondo DataFrame utilizzando la colonna 'Referente' come chiave.

    Args:
        main_dataframe (pd.DataFrame): Il DataFrame principale contenente la colonna 'Referente'.
        second_dataframe (pd.DataFrame): Il secondo DataFrame contenente i dettagli delle referenze.

    Returns:
        pd.DataFrame: DataFrame aggiornato con le colonne 'Nome', 'Quantita in grammi' e 'Pezzi in un cartone' aggiunte.
    """
    try:
        # Verifica se le colonne richieste esistono nel secondo DataFrame
        required_columns = ['Referente', 'Nome', 'Quantita in grammi', 'Pezzi in un cartone', 'Ricetta', 'Listino']
        for col in required_columns:
            if col not in second_dataframe.columns:
                raise KeyError(f"La colonna '{col}' non è presente nel secondo DataFrame.")
        
        # Forza entrambi i DataFrame a trattare 'Referente' come stringa
        main_dataframe['Referente'] = main_dataframe['Referente'].astype(str)
        second_dataframe['Referente'] = second_dataframe['Referente'].astype(str)

        # Unione dei DataFrame basata sulla colonna 'Referente'
        merged_dataframe = main_dataframe.merge(
            second_dataframe[required_columns],
            on='Referente',
            how='left'
        )

        
        

        return merged_dataframe

    except KeyError as e:
        print(f"Errore di colonna: {e}")
        return main_dataframe

    except Exception as e:
        print(f"Errore durante l'unione dei DataFrame: {e}")
        return main_dataframe


#funzione per creare grafico ad anello
def grafico_ad_anello(percentuale, titolo="Percentuale"):
    """
    Crea un grafico ad anello con un valore percentuale al centro.

    Args:
        percentuale (int): Valore percentuale da rappresentare.
        titolo (str): Titolo del grafico.

    Returns:
        plotly.graph_objects.Figure: Oggetto del grafico Plotly.
    """
    # Gestione di valori fuori dal range
    if percentuale < 0:
        percentuale = 0
    elif percentuale > 100:
        percentuale = 100

    # Dati del grafico
    valori = [percentuale, 100 - percentuale]
    etichette = ["", ""]

    # Creazione del grafico
    fig = go.Figure(data=[
        go.Pie(
            values=valori,
            labels=etichette,
            hole=0.7,  # Rende il grafico un anello
            marker=dict(colors=["#636EFA", "#E5ECF6"]),
            showlegend=False,
            textinfo="none"
        )
    ])

    # Aggiunta del testo al centro dell'anello
    fig.add_annotation(
        text=f"<b>{percentuale:.2f}%</b>",
        x=0.5, y=0.5,
        font=dict(size=20, color="#000"),
        showarrow=False
    )

    # Impostazioni del layout
    fig.update_layout(
        title=dict(
            text=titolo,
            x=0.5,
            font=dict(size=15)
        ),
        margin=dict(t=20, b=20, l=20, r=20),
        height=300,
        width=300
    )

    return fig



#funzione per creare grafico a barre orizzontali 
def grafico_margine_totale_e_promozione(margine1, margine2):
    """
    Funzione per visualizzare un grafico a barre orizzontali con margini in euro utilizzando Plotly e Streamlit.
    
    Parametri:
    - margine1 (float): Primo margine.
    - margine2 (float): Secondo margine.
    """
    
    # Etichette delle categorie e valori
    categorie = ['Margine A.P.', 'Margine Promozione']
    valori = [margine1, margine2]

    # Creazione del grafico a barre orizzontali
    fig = go.Figure(go.Bar(
        x=valori,
        y=categorie,
        orientation='h',  # Barre orizzontali
        marker_color=['#1f77b4', '#ff7f0e']  # Colori delle barre
    ))

    # Layout del grafico
    fig.update_layout(
        title="",
        xaxis_title="Margine in euro (€)",
        yaxis_title="",
        xaxis=dict(
            tickformat="€,",  # Formatta l'asse x con il simbolo dell'euro
            showgrid=True,  # Linee della griglia
        ),
        template="plotly_white",  # Tema chiaro
        height=300,
    )

    # Mostra il grafico nella dashboard Streamlit
    st.plotly_chart(fig, use_container_width=True)


def grafico_andamentoo_del_margine(margine1, margine2, margine3, margine4, fatturato1, fatturato2):
    """
    Funzione per visualizzare un grafico a barre orizzontali con margini in euro utilizzando Plotly e Streamlit.
    
    Parametri:
    - margine1 (float): Primo margine.
    - margine2 (float): Secondo margine.
    """
    
    # Etichette delle categorie e valori
    categorie = ['Margine I° Liv. A.P.','Margine II° liv. A.P.', 'Fatturato A.P.', 'Margine Promozione', 'Margine promozione II° Liv.', 'Fatturato Promozione']
    valori = [margine1, margine2, fatturato1, margine3, margine4, fatturato2]

    # Creazione del grafico a barre orizzontali
    fig = go.Figure(go.Bar(
        x=categorie,
        y=valori,
        marker_color=['#1f77b4', '#ff7f0e']  # Colori delle barre
    ))

    # Layout del grafico
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="(€)",
        yaxis=dict(
            tickformat="€,",  # Formatta l'asse x con il simbolo dell'euro
            showgrid=True,  # Linee della griglia
        ),
        template="plotly_white",  # Tema chiaro
        height=300,
    )

    # Mostra il grafico nella dashboard Streamlit
    st.plotly_chart(fig, use_container_width=True)



#funzione per visualizzare dashboard interattiva
def show_dashboard(dataframe):
    """
    Mostra una dashboard interattiva utilizzando Streamlit per visualizzare il DataFrame.

    Args:
        dataframe (pd.DataFrame): Il DataFrame da visualizzare nella dashboard.
    """
   
    st.title("Calcolatore Promozioni clienti")
    
    
    with st.sidebar:
        st.markdown("### 🔍 Filtro Dati")
        
        # Filtro Cliente
        cliente_options = ["Tutti"] + list(dataframe['Cliente'].dropna().unique())
        cliente_filter = st.selectbox("Seleziona un cliente:", options=cliente_options)
        
        # Filtro Nome
        nome_options = ["Tutti"] + list(dataframe['Nome'].dropna().unique())
        nome_filter = st.selectbox("Seleziona un Nome:", options=nome_options)
        
        # Filtro Grammatura
        quantita_options = ["Tutti"] + list(dataframe['Quantita in grammi'].dropna().unique())
        quantita_gr = st.selectbox("Seleziona grammatura(gr):", options=quantita_options)
        
        # Filtro Date
        start_date = st.date_input("Seleziona la data di inizio:", value=pd.to_datetime("2024-01-01")).strftime('%Y-%m-%d')
        end_date = st.date_input("Seleziona la data di fine:", value=pd.to_datetime("2024-12-31")).strftime('%Y-%m-%d')

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    dataframe['Data_datetime'] = pd.to_datetime(dataframe['Data'], format='%m/%Y', errors='coerce')

    # Applicazione dei filtri con l'opzione "Tutti"
    filtered_data = dataframe[
        ((dataframe['Cliente'] == cliente_filter) | (cliente_filter == "Tutti")) &
        ((dataframe['Nome'] == nome_filter) | (nome_filter == "Tutti")) &
        ((dataframe['Quantita in grammi'] == quantita_gr) | (quantita_gr == "Tutti")) &
        (dataframe['Data_datetime'] >= start_date) &
        (dataframe['Data_datetime'] <= end_date)
    ]

    if 'Nome' not in dataframe.columns:
        st.error("La colonna 'Nome' non è presente nel DataFrame. Verificare l'unione dei dati.")
        return
    
    
    # **Aggiungi il selettore di sconto con layout a colonne**
    sconto = 0
    
    col01, col02, col03, col4 = st.columns([1, 1, 1, 1])  # Configura la larghezza delle colonne

    with col01:  # Posiziona il selettore nella colonna 
        st.write("### Sconto Applicabile")
        sconto = st.slider("Seleziona lo sconto da applicare (%)", min_value=-70, max_value=70, value=0)
    
    
    # **Aggiungi il selettore di sconto con layout a colonne**
    incremento = 0
    
    with col02:
        # Aggiunta del menu a tendina con due opzioni per eliminare le promo del anno precedente 
        st.markdown("### 🔽 elimina promozione A.p.")
        azione_promozione = st.selectbox(
            "Seleziona un'azione per la promozione:",
            options=["No", "Si"]
        )

        
            
    

    with col4:  # Posiziona il selettore nella colonna 
    
        st.write("### Incremento Vendite")    
        incremento = st.slider("Seleziona l'icremento di cartoni venduti(%)", min_value=0, max_value=200, value=0)

    st.divider()
    
    
    # Calcola i KPI usando la funzione calcolo_KPI
    (filtered_data, fatturato, margine_pezzo, margine_pezzo_ap, margine_cartone, margine_cartone_ap,
     margine_totale, margine_totale_ap, cartoni_venduti, cartoni_venduti_ap,
     pezzi_venduti, pezzi_venduti_ap, prezzo_cartone, prezzo_pezzo,
     costo_cartone, costo_pezzo, costo_totale, prezzo_listino, sconto_applicato, sconto_secondo_livello,
     prezzo_cartone_scontato, prezzo_pezzo_scontato, fatturato_scontato, sconto_prezzo_listino, 
     margine_pezzo_scontato, margine_cartone_scontato, 
     margine_totale_scontato, fatturato_con_sconto_incremento, 
     cartoni_venduti_con_incremento, 
     margine_totale_scontato_con_incremento, fatturato_sconto_secondo_livello,
     margine_totale_con_sconto_secondo_livello, fatturato_con_sconto_incremento_e_sconto_secondo_livello,
     margine_totale_scontato_con_incremento_e_sconto_secondo_livello, 
     sconto_primo_livello,fatturato_ap_eliminata_promo,
     margine_ap_eliminata_promo, fatturato_ap_eliminata_promo_con_sconto_secondo_liv, 
     margine_ap_eliminata_promo_con_sconto_secondo_liv) = calcolo_KPI(filtered_data, sconto, incremento)
    
    # Prima riga: Margine totale, Margine totale AP, Grafico a barre
    
    col1, col2, col3 = st.columns([1,1,2])

    # Colonna 1: Metriche A.p. 
    # Aggiunta della visualizzazione condizionale nella colonna 1
    with col1:
        if azione_promozione == "No":
            st.write("##### Anno precedente")
            st.metric("💰 Fatturato", f"€ {fatturato:,.0f}")
            st.metric("📈 Cartoni venduti", f" {cartoni_venduti:,.0f}")
            st.metric("📈 Margine dopo sconto canale", f"€ {margine_totale:,.0f}")
            st.metric("💰 Fatturato con sconto di secondo livello", f"€ {fatturato_sconto_secondo_livello:,.0f}")
            st.metric("📈 Margine Totale con sconto di secondo livello", f"€ {margine_totale_con_sconto_secondo_livello:,.0f}")
        elif azione_promozione == "Si":
            st.write("##### Dati A.p. senza promozione")
            st.metric("💰 Fatturato A.p. senza promozione", f"€ {fatturato_ap_eliminata_promo:,.0f}")
            st.metric("📈 Cartoni venduti senza promozione", f" {cartoni_venduti_ap:,.0f}")
            st.metric("📈 Margine A.p. senza promozione", f"€ {margine_ap_eliminata_promo:,.0f}")
            st.metric("💰 Fatturato con sconto di secondo livello", f"€ {fatturato_ap_eliminata_promo_con_sconto_secondo_liv:,.0f}")
            st.metric("📈 Margine Totale con sconto di secondo livello", f"€ {margine_ap_eliminata_promo_con_sconto_secondo_liv:,.0f}")


    # Colonna 2: Metriche Promozione
    with col2:
        st.write("##### Promozione")
        st.metric("💰 Fatturato", f"€ {fatturato_con_sconto_incremento:,.0f}")    
        st.metric("📈 Cartoni venduti", f" {cartoni_venduti_con_incremento:,.0f}")
        st.metric("📈 Margine dopo promozione", f"€ {margine_totale_scontato_con_incremento:,.0f}")
        st.metric("💰 Fatturato con sconto di secondo livello", f"€ {fatturato_con_sconto_incremento_e_sconto_secondo_livello:,.0f}")
        st.metric("📈 Margine Totale con sconto di secondo livello", f"€ {margine_totale_scontato_con_incremento_e_sconto_secondo_livello:,.0f}")

        
        
    with col3:
        col01, col02, col03 = st.columns([1,1,1])
        with col01:
            st.metric("📉 Sconto anno prec. (I° Livello)", f"{sconto_applicato:,.2f} %")
            st.metric("📉 Sconto canale standard", f"{sconto_primo_livello:,.2f} %")
            
        with col02:
            st.metric("📉 Sconto Promozione (I° Livello)", f"{sconto_prezzo_listino:,.2f} %")
        with col03:
            st.metric("📉 Sconto di II° livello", f"{sconto_secondo_livello:,.2f} %")
   
        #fig = grafico_ad_anello(sconto_applicato, titolo="Sconto Applicato")
        #st.plotly_chart(fig, use_container_width=True)
        grafico_margine_totale_e_promozione(margine_totale_con_sconto_secondo_livello, 
                                            margine_totale_scontato_con_incremento_e_sconto_secondo_livello)
        #grafico_andamentoo_del_margine(margine_totale, margine_totale_con_sconto_secondo_livello,
                                       #margine_totale_scontato_con_incremento,
                                       #margine_totale_scontato_con_incremento_e_sconto_secondo_livello, 
                                       #fatturato, fatturato_con_sconto_incremento)
        
    st.divider()




    # Seconda riga: Prezzi e costi
    st.write("### Prezzi e Costi")
    col4, col5, col6, col7 = st.columns(4)
    col4.metric("📦 Prezzo Cartone", f"€ {prezzo_cartone:,.2f}")
    col5.metric("🛒 Prezzo Pezzo", f"€ {prezzo_pezzo:,.2f}")
    col6.metric("💸 Costo Cartone", f"€ {costo_cartone:,.2f}")
    col7.metric("💳 Costo Pezzo", f"€ {costo_pezzo:,.2f}")

    # Terza riga: Margini
    st.write("### Margini e Vendite")
    col8, col9, col10, col11 = st.columns(4)
    col8.metric("📦 Margine Cartone", f"€ {margine_cartone:,.2f}")
    col9.metric("🛒 Margine Pezzo", f"€ {margine_pezzo:,.2f}")
    col10.metric("📦 Cartoni Venduti", f"{cartoni_venduti:,.0f}")
    col11.metric("🛒 Pezzi Venduti", f"{pezzi_venduti:,.0f}")

    # Quarta riga: Margini anno precedente
    st.write("### Vendite Anno Precedente")
    col12, col13, col14, col15 = st.columns(4)
    col12.metric("📦 Margine Cartone AP", f"€ {margine_cartone_ap:,.2f}")
    col13.metric("🛒 Margine Pezzo AP", f"€ {margine_pezzo_ap:,.2f}")
    col14.metric("📦 Cartoni Venduti AP", f"{cartoni_venduti_ap:,.0f}")
    col15.metric("🛒 Pezzi Venduti AP", f"{pezzi_venduti_ap:,.0f}")


#Funzione per il calcolo dei KPI
def calcolo_KPI(dataframe, sconto, incremento):
    """
    Calcola i KPI principali e restituisce i risultati aggregati.

    Args:
        dataframe (pd.DataFrame): Il DataFrame contenente i dati.
        sconto (float): Percentuale di sconto da applicare.

    Returns:
        tuple: Valori calcolati dei KPI.
    """
    # Creare una copia esplicita del DataFrame
    dataframe = dataframe.copy()

    # Conversione delle colonne necessarie in valori numerici
    colonne_da_convertire = [
        'Pezzi in un cartone', 'Cartoni_Venduti', 'Cartoni_Venduti_Prec',
        'Fatturato', 'Fatturato_Anno_Prec', 'Ricetta', 'Listino'
    ]
    for col in colonne_da_convertire:
        if col in dataframe.columns:
            dataframe[col] = pd.to_numeric(dataframe[col], errors='coerce').fillna(0)

    # Modifiche al DataFrame usando `.loc`
    dataframe.loc[:, 'pezzi_venduti'] = dataframe['Pezzi in un cartone'] * dataframe['Cartoni_Venduti']
    dataframe.loc[:, 'pezzi_venduti_ap'] = dataframe['Pezzi in un cartone'] * dataframe['Cartoni_Venduti_Prec']

    dataframe.loc[:, 'prezzo_pezzo_venduto'] = dataframe['Fatturato'] / dataframe['pezzi_venduti'].replace(0, 1)
    dataframe.loc[:, 'prezzo_pezzo_venduto_ap'] = dataframe['Fatturato_Anno_Prec'] / dataframe['pezzi_venduti_ap'].replace(0, 1)

    dataframe.loc[:, 'prezzo_cartone_venduto'] = dataframe['Fatturato'] / dataframe['Cartoni_Venduti'].replace(0, 1)
    dataframe.loc[:, 'prezzo_cartone_venduto_ap'] = dataframe['Fatturato_Anno_Prec'] / dataframe['Cartoni_Venduti_Prec'].replace(0, 1)

    dataframe.loc[:, 'costo_cartone'] = dataframe['Pezzi in un cartone'] * dataframe['Ricetta']
    dataframe.loc[:, 'costo_totale'] = dataframe['pezzi_venduti'] * dataframe['Ricetta']

    dataframe.loc[:, 'margine_pezzo'] = dataframe['prezzo_pezzo_venduto'] - dataframe['Ricetta']
    dataframe.loc[:, 'margine_cartone'] = dataframe['prezzo_cartone_venduto'] - dataframe['costo_cartone']
    dataframe.loc[:, 'margine_totale'] = dataframe['Fatturato'] - dataframe['costo_totale']

    dataframe.loc[:, 'margine_pezzo_ap'] = dataframe['prezzo_pezzo_venduto_ap'] - dataframe['Ricetta']
    dataframe.loc[:, 'margine_cartone_ap'] = dataframe['prezzo_cartone_venduto_ap'] - dataframe['costo_cartone']
    dataframe.loc[:, 'margine_totale_ap'] = dataframe['Fatturato_Anno_Prec'] - dataframe['costo_totale']

    # Calcolo dei risultati aggregati
    fatturato = dataframe['Fatturato'].sum()
    margine_pezzo = dataframe['margine_pezzo'].mean()
    margine_pezzo_ap = dataframe['margine_pezzo_ap'].mean()
    margine_cartone = dataframe['margine_cartone'].mean()
    margine_cartone_ap = dataframe['margine_cartone_ap'].mean()
    margine_totale = dataframe['margine_totale'].sum()
    margine_totale_ap = dataframe['margine_totale_ap'].sum()
    cartoni_venduti = dataframe['Cartoni_Venduti'].sum()
    cartoni_venduti_ap = dataframe['Cartoni_Venduti_Prec'].sum()
    pezzi_venduti = dataframe['pezzi_venduti'].sum()
    pezzi_venduti_ap = dataframe['pezzi_venduti_ap'].sum()
    prezzo_cartone = dataframe['prezzo_cartone_venduto'].mean()
    prezzo_pezzo = dataframe['prezzo_pezzo_venduto'].mean()
    costo_cartone = dataframe['costo_cartone'].mean()
    costo_pezzo = dataframe['Ricetta'].mean()
    costo_totale = dataframe['costo_totale'].sum()
    prezzo_listino = dataframe['Listino'].mean()
    sconto_secondo_livello = dataframe['Sconto secondo livello'].mean()
    sconto_primo_livello = dataframe['Sconto primo livello'].mean()


    

    # Calcolo sconto e margini con sconto e incremento del numero di cartoni
    prezzo_pezzo = fatturato / pezzi_venduti
    prezzo_cartone = fatturato / cartoni_venduti
    costo_pezzo = costo_totale / pezzi_venduti
    costo_cartone = costo_totale / cartoni_venduti
    sconto_applicato = (1 - prezzo_pezzo / prezzo_listino) * 100   #sconto di primo livello
    prezzo_cartone_scontato = prezzo_cartone * (100 - sconto) / 100
    prezzo_pezzo_scontato = prezzo_pezzo * (100 - sconto) / 100   #prezzo scontato con lo sconto inserito nella dashboard
    fatturato_scontato = fatturato * (100 - sconto) / 100
    sconto_prezzo_listino = (1 - prezzo_pezzo_scontato / prezzo_listino) * 100   #sconto finale di primo livello sul fatturato
    margine_pezzo_scontato = prezzo_pezzo_scontato - costo_pezzo
    margine_cartone_scontato = prezzo_cartone_scontato - costo_cartone
    margine_totale_scontato = fatturato_scontato - costo_totale
    cartoni_venduti_con_incremento = cartoni_venduti * (100 + incremento) / 100
    fatturato_con_sconto_incremento = cartoni_venduti_con_incremento * prezzo_cartone_scontato
    margine_totale_scontato_con_incremento = fatturato_con_sconto_incremento - (costo_cartone * cartoni_venduti_con_incremento)
    
    
    #KPI A.p. senza promozioni 
    fatturato_ap_eliminata_promo = (100-sconto_primo_livello)/100 * (pezzi_venduti * prezzo_listino)
    margine_ap_eliminata_promo = fatturato_ap_eliminata_promo - costo_totale
    
    
    #KPI con sconto di secondo livello
    fatturato_sconto_secondo_livello = fatturato * (100 - sconto_secondo_livello) / 100
    margine_totale_con_sconto_secondo_livello = fatturato_sconto_secondo_livello - costo_totale
    fatturato_con_sconto_incremento_e_sconto_secondo_livello = fatturato_con_sconto_incremento * (100 - sconto_secondo_livello) / 100
    margine_totale_scontato_con_incremento_e_sconto_secondo_livello = fatturato_con_sconto_incremento_e_sconto_secondo_livello - (costo_cartone * cartoni_venduti_con_incremento)
    fatturato_ap_eliminata_promo_con_sconto_secondo_liv = fatturato_ap_eliminata_promo * (100 - sconto_secondo_livello) / 100
    margine_ap_eliminata_promo_con_sconto_secondo_liv = fatturato_ap_eliminata_promo_con_sconto_secondo_liv - costo_totale

    return (dataframe, fatturato, margine_pezzo, margine_pezzo_ap, margine_cartone, margine_cartone_ap, margine_totale, 
            margine_totale_ap, cartoni_venduti, cartoni_venduti_ap, pezzi_venduti, pezzi_venduti_ap, prezzo_cartone, 
            prezzo_pezzo, costo_cartone, costo_pezzo, costo_totale, prezzo_listino, sconto_applicato, sconto_secondo_livello, 
            prezzo_cartone_scontato, prezzo_pezzo_scontato, fatturato_scontato, sconto_prezzo_listino, 
            margine_pezzo_scontato, margine_cartone_scontato, margine_totale_scontato, fatturato_con_sconto_incremento, 
            cartoni_venduti_con_incremento, margine_totale_scontato_con_incremento, fatturato_sconto_secondo_livello,
            margine_totale_con_sconto_secondo_livello, fatturato_con_sconto_incremento_e_sconto_secondo_livello,
            margine_totale_scontato_con_incremento_e_sconto_secondo_livello, sconto_primo_livello, fatturato_ap_eliminata_promo,
            margine_ap_eliminata_promo, fatturato_ap_eliminata_promo_con_sconto_secondo_liv, 
            margine_ap_eliminata_promo_con_sconto_secondo_liv)


# MAIN
st.title("Caricamento File Excel")

# Carica più file Excel
uploaded_files = st.file_uploader("Carica i file Excel", type=["xlsx"], accept_multiple_files=True)

# Controlla se l'utente ha caricato almeno un file
if uploaded_files:
    # Processa i file caricati
    dataframes, details_dataframe = process_uploaded_files(uploaded_files)

    # Combina i dati dei clienti in un unico DataFrame
    main_dataframe = pd.concat(dataframes, ignore_index=True)

    # Unisce con i dettagli delle referenze, se presenti
    if not details_dataframe.empty:
        main_dataframe = merge_with_second_dataframe(main_dataframe, details_dataframe)

    # Mostra la dashboard con i dati elaborati
    show_dashboard(main_dataframe)
else:
    st.warning("⚠️ Carica almeno un file per continuare.")





