# Tenuta Turrita · Quote Manager

Gestionale professionale per la pianificazione gastronomica, stesura contrattuale, generazione documentale PDF di lusso e trasmissione preventivi per **Tenuta Turrita** (Villa per matrimoni ed eventi).

---

## Indice dei Contenuti

- [Panoramica](#panoramica)
- [Funzionalità Principali](#funzionalità-principali)
- [Architettura del Sistema](#architettura-del-sistema)
- [Requisiti di Sistema](#requisiti-di-sistema)
- [Guida all'Installazione & Avvio](#guida-allinstallazione--avvio)
  - [Avvio Rapido su macOS (Doppio Clic)](#avvio-rapido-su-macos-doppio-clic)
  - [Avvio Standard da Terminale](#avvio-standard-da-terminale)
- [Moduli Operativi](#moduli-operativi)
  - [Archivio & Ricerca Preventivi](#archivio--ricerca-preventivi)
  - [Modelli Gastronomici & Composizione Menù](#modelli-gastronomici--composizione-menù)
  - [Prospetto Economico & Calcolo Fiscale](#prospetto-economico--calcolo-fiscale)
  - [Motore di Stampa Web & PDF Luxury](#motore-di-stampa-web--pdf-luxury)
  - [Trasmissione Email Multipart](#trasmissione-email-multipart)
  - [Condizioni Contrattuali & Caparra](#condizioni-contrattuali--caparra)
  - [Backup Transazionale & Disaster Recovery](#backup-transazionale--disaster-recovery)
- [Suite di Test Automatizzati](#suite-di-test-automatizzati)
- [Struttura della Repository](#struttura-della-repository)
- [Linee Guida di Sicurezza](#linee-guida-di-sicurezza)
- [Licenza](#licenza)

---

## Panoramica

**Tenuta Turrita Quote Manager** è progettato per gestire il ciclo di vita completo della proposta commerciale per ricevimenti di nozze, cerimonie ed eventi privati. L'applicazione garantisce un'estetica di pregio, calcoli fiscali rigorosi, impaginazione multipagina automatica e tracciamento documentale completo.

### Identità Visiva Istituzionale

| Parametro | Valore |
|---|---|
| Nome Struttura | Tenuta Turrita |
| Payoff Ufficiale | Villa per matrimoni ed eventi |
| Sede | Via Roma, Dragoni (CE) |
| Recapito Telefonico | +39 320 688 3788 |
| Verde Salvia Principale | `#87977A` |
| Verde Scuro Accento | `#6F8062` |
| Oro Caldo Finiture | `#DDBA74` |
| Sfondo Caldo | `#F6F3EC` |
| Testo Istituzionale | `#2F352C` |

---

## Funzionalità Principali

- **Gestione Multi-Intestatario**: Supporto completo per primo referente (es. Sposo) e secondo intestatario (es. Sposa), con ruoli, codici fiscali, residenze e recapiti differenziati.
- **Modelli Gastronomici Predefiniti**: Caricamento in un clic di menù degustazione studiati per matrimoni di gala, cerimonie tradizionali ed eventi speciali.
- **Composizione Interattiva Portate**: Suddivisione distinta tra *Menù Adulti* e *Menù Bambini*, con riordinamento portate in tempo reale (`Su` / `Giù`), allergeni e note di sala.
- **Scomposizione Economica Analitica**: Calcolo istantaneo di quota adulti, quota bambini, servizi extra, sconti riservati, totale imponibile netto e imposta IVA.
- **Generazione PDF Luxury (ReportLab)**: Layout A4 professionale a due passate con `NumberedCanvas` ("Pagina X di Y"), logo in alta definizione e blocchi protetti `KeepTogether` anti-rottura pagina.
- **Modulo di Stampa Browser**: Foglio di stampa con foglio stile dedicato `@media print`.
- **Invio Email Brandizzate**: Client SMTP integrato con invio simultaneo di template HTML formattato con i colori della Tenuta, testo in chiaro e allegato PDF compilato in tempo reale.
- **Registro Storico Email & PDF**: Tracciamento di ogni versione PDF generata e di ogni trasmissione email verso il cliente.
- **Backup Transazionale SQLite**: Sincronizzazione atomica a caldo tramite API nativa `sqlite3.Connection.backup()`, con archivio compresso ZIP e opzione di caricamento cloud su Google Drive.

---

## Architettura del Sistema

```text
[ Browser Client ]
       │
       ▼
[ FastAPI Application Server (Uvicorn) ]
  ├── Template Engine: Jinja2
  ├── REST APIs: /api/presets, /quotes, /backup, /settings
  ├── Quote Engine: calculate_quote_breakdown(), MENU_PRESETS
  ├── PDF Engine: ReportLab (NumberedCanvas, KeepTogether)
  ├── Email Service: SMTP Multipart (MIME Text + HTML + PDF Attachment)
  └── Backup Service: SQLite Native Backup API + Google Drive OAuth API
       │
       ▼
[ Database Transazionale: SQLite3 (ACID) ]
```

---

## Requisiti di Sistema

- **Python**: Versione 3.10 o superiore (testato su Python 3.11, 3.12, 3.13 e 3.14).
- **Sistema Operativo**: macOS, Linux o Windows.
- **Browser Web**: Google Chrome, Safari, Mozilla Firefox o Microsoft Edge.

---

## Guida all'Installazione & Avvio

### 1. Clonazione del Repository

```bash
git clone https://github.com/melillopietro/tenuta-turrita-quote-manager.git
cd tenuta-turrita-quote-manager
```

### 2. Creazione dell'Ambiente Virtuale & Dipendenze

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Avvio Rapido su macOS (Doppio Clic)

Su macOS è disponibile lo script di lancio diretto:

1. Aprire la cartella di progetto nel **Finder**.
2. Fare doppio clic su **`avvia_mac.command`**.
3. Il server si avvierà in automatico e aprirà la pagina iniziale nel browser all'indirizzo **`http://127.0.0.1:8000`**.

---

### Avvio Standard da Terminale

Con lo script di avvio integrato (con auto-rilevamento dell'ambiente virtuale):

```bash
./run_local.py
```

Oppure tramite **Uvicorn**:

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Dashboard Gestionale**: `http://127.0.0.1:8000`
- **Documentazione Interattiva API (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **Documentazione Alternativa (ReDoc)**: `http://127.0.0.1:8000/redoc`

---

## Moduli Operativi

### Archivio & Ricerca Preventivi
La schermata principale dell'archivio offre:
- **Ricerca full-text**: Filtra su nominativo cliente, codice preventivo, recapito telefonico, indirizzo email o location.
- **Filtri combinati**: Selezione per tipologia evento, anno di competenza e ordinamento (cronologico, data evento, importo preventivo).
- **Tab di stato rapido**: Contatori dinamici per lo stato del preventivo (*Tutti*, *Bozza*, *Inviato*, *In attesa*, *Accettato*, *Rifiutato*, *Scaduto*, *Annullato*).

### Modelli Gastronomici & Composizione Menù
Il selettore include i modelli di degustazione studiati dalla Tenuta:
- *Matrimonio Grand Galà* (Aperitivo a buffet, crudité di mare, astice, pescato nobile e torta monumentale).
- *Cerimonia Tradizione & Terra* (Antipasto nobile campano, calamarata con chianina e porcini, tagliata di manzo).
- *Festa & Anniversario* (Finger food di benvenuto, risotto mantecato, grigliata mista e sweet table).

### Prospetto Economico & Calcolo Fiscale
Scomposizione automatica conforme agli standard contabili:
- `Subtotale Adulti` = *Numero Ospiti Adulti × Quota Unitaria Adulto*
- `Subtotale Bambini` = *Numero Ospiti Bambini × Quota Unitaria Bambino*
- `Totale Imponibile Netto` = *Subtotale Adulti + Subtotale Bambini + Extra - Sconto*
- `Imposta IVA` = *(Totale Imponibile Netto × Aliquota IVA) / 100*
- `Totale Complessivo Preventivo` = *Totale Imponibile Netto + Imposta IVA*

### Motore di Stampa Web & PDF Luxury
- Intestazione simmetrica con logo ad alta risoluzione.
- Prospetto economico ordinato.
- Protezione da pagine orfane mediante `KeepTogether`.
- Footer dinamico con conteggio totale delle pagine calcolato a due passate.

### Trasmissione Email Multipart
- Invio tramite server SMTP aziendale con supporto SSL/TLS.
- Doppio canale di rendering:
  1. Plain-text formale per client testuali o anteprime veloci.
  2. HTML responsive con impaginazione grafica Tenuta Turrita, tabella riassuntiva e firma istituzionale.
- Allegato PDF compilato al momento dell'invio.

### Backup Transazionale & Disaster Recovery
- Utilizzo dell'API nativa `sqlite3.Connection.backup()`, che copia il database senza rischio di lock o corruzione dati.
- Creazione di archivio ZIP compresso contenente database e tutti i file PDF.
- Integrazione con Google Drive via OAuth2 (posizionando le credenziali in `app/secrets/google_credentials.json`).

---

## Suite di Test Automatizzati

Il progetto include una suite di collaudo automatizzata con **`pytest`** che verifica la corretta esecuzione di:
- Calcoli matematici e fiscali del preventivo (`test_calculate_quote_breakdown`).
- Operazioni CRUD, cambio stato e duplicazione progressiva (`test_quote_crud_and_duplication`).
- Filtri di ricerca full-text e per stato (`test_list_quotes_filters`).
- Generazione conforme e validazione header PDF (`test_pdf_generation`).
- Backup locale transazionale SQLite (`test_backup_service`).
- Endpoint web e rendering template (`test_fastapi_endpoints`).

### Esecuzione della Suite

```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

Risultato atteso:
```text
tests/test_app.py::test_calculate_quote_breakdown PASSED                 [ 16%]
tests/test_app.py::test_quote_crud_and_duplication PASSED                [ 33%]
tests/test_app.py::test_list_quotes_filters PASSED                       [ 50%]
tests/test_app.py::test_pdf_generation PASSED                            [ 66%]
tests/test_app.py::test_backup_service PASSED                            [ 83%]
tests/test_app.py::test_fastapi_endpoints PASSED                         [100%]

======================== 6 passed in 0.30s ========================
```

---

## Struttura della Repository

```text
tenuta-turrita-quote-manager/
├── app/
│   ├── main.py                  # Router principale FastAPI, Lifespan e middleware
│   ├── db.py                    # Gestore connessione SQLite, inizializzazione schema
│   ├── services/
│   │   ├── quote_service.py     # Logica di business, modelli gastronomici e calcoli
│   │   ├── pdf_service.py       # Motore ReportLab luxury con NumberedCanvas
│   │   ├── email_service.py     # Client SMTP multipart (HTML + Text + PDF)
│   │   └── backup_service.py    # Backup transazionale SQLite e sync Google Drive
│   ├── static/
│   │   ├── style.css            # Fogli di stile istituzionali Tenuta Turrita
│   │   ├── tenuta_turrita_logo.png
│   │   └── tenuta_turrita_logo.svg
│   ├── templates/
│   │   ├── base.html            # Layout master, navigazione e toast notification
│   │   ├── dashboard.html       # Statistiche e preventivi recenti
│   │   ├── quotes.html          # Archivio preventivi, filtri e ricerca avanzata
│   │   ├── quote_form.html      # Creazione nuovo preventivo con modelli
│   │   ├── quote_edit.html      # Modifica preventivo e riordino portate
│   │   ├── quote_detail.html    # Scheda analitica, storico email e PDF
│   │   ├── quote_print.html     # Layout di stampa A4 (@media print)
│   │   ├── send_form.html       # Compositore e trasmissione email
│   │   ├── contract_form.html   # Configurazione clausole contrattuali
│   │   ├── settings.html        # Configurazione struttura e SMTP
│   │   └── backup.html          # Gestione archivi e sincronizzazione cloud
│   └── secrets/
│       └── .gitkeep             # Directory protetta per credenziali OAuth
├── data/                        # Directory locale non tracciata per database e archivi
│   ├── pdfs/                    # File PDF generati
│   └── backups/                 # Archivi compressi di backup
├── tests/
│   └── test_app.py              # Suite di test automatizzati pytest
├── avvia_mac.command            # Launcher con doppio clic per macOS Finder
├── run_local.py                 # Script di avvio con auto-rilevamento venv
├── requirements.txt             # Dipendenze Python
├── .gitignore                   # Regole di esclusione dati sensibili
└── README.md                    # Documentazione tecnica istituzionale
```

---

## Linee Guida di Sicurezza

- **Protezione Dati Personali**: I database generati (`data/*.db`), i preventivi in PDF (`data/pdfs/*.pdf`) e gli archivi di backup (`data/backups/*.zip`) contengono dati sensibili dei clienti e sono esclusi dal tracciamento Git tramite `.gitignore`.
- **Credenziali Riservate**: Le password SMTP e i token di accesso a Google Drive (`app/secrets/google_credentials.json`, `data/google_token.json`) non devono mai essere inclusi nei commit.
- **Distribuzione in Produzione**: In caso di pubblicazione su server pubblico esposto a Internet, si raccomanda l'uso di un reverse proxy (es. Nginx o Caddy) con terminazione SSL/HTTPS e l'abilitazione di un layer di autenticazione con sessioni protette.

---

## Licenza

Progetto proprietario sviluppato per la gestione operativa dei preventivi di **Tenuta Turrita**. Tutti i diritti riservati.
