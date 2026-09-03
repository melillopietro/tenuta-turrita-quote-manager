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

## Guida all'Installazione & Avvio Rapido (Zero-Setup)

L'applicazione è dotata di script intelligenti di auto-provisioning per **Windows (10 e 11)**, **macOS** e **Linux**: se Python non è presente sul computer, lo script lo scarica, lo installa silenziosamente, configura l'ambiente virtuale con tutte le dipendenze e avvia il gestionale aprendo il browser in automatico.

---

### 🪟 Windows 10 & 11 (Doppio Clic Automatico)

1. Scarica o clona la cartella del progetto.
2. Fai doppio clic su **`avvia_windows.bat`**.
3. **Al primo avvio**: se Python non è presente nel sistema, lo script PowerShell integrato (`scripts/setup_windows.ps1`) scarica e installa automaticamente Python da `python.org`, configura l'ambiente `.venv`, installa le librerie e apre il browser su `http://127.0.0.1:8000`.
4. **Agli avvii successivi**: l'avvio è istantaneo in meno di 2 secondi.

> **Eseguibile Standalone `.exe`**: Se preferisci non avere cartelle di codice sorgente, puoi scaricare l'eseguibile pronto all'uso `TenutaTurritaQuoteManager-Windows.zip` dalla sezione **Actions / Releases** di GitHub.

---

### 🍏 macOS (Doppio Clic Automatico)

1. Aprire la cartella di progetto nel **Finder**.
2. Fare doppio clic su **`avvia_mac.command`**.
3. Se Python non è presente, lo script predispone il download ufficiale. Crea automaticamente l'ambiente `.venv`, installa le dipendenze e avvia il browser.

---

### 🐧 Linux (Ubuntu, Debian, Fedora, Arch)

1. Aprire il terminale nella cartella del progetto.
2. Eseguire lo script:
   ```bash
   ./avvia_linux.sh
   ```
3. Lo script rileva la distribuzione Linux, assicura la presenza di `python3` e `python3-venv`, crea `.venv` e avvia il browser predefinito.

---

### 💻 Avvio Manuale da Terminale (Tutti i Sistemi Operativi)

```bash
git clone https://github.com/melillopietro/tenuta-turrita-quote-manager.git
cd tenuta-turrita-quote-manager
python3 -m venv .venv
source .venv/bin/activate    # Su Windows: .venv\Scripts\activate
pip install -r requirements.txt
./run_local.py               # Oppure: python desktop_app.py
```

- **Dashboard Gestionale**: `http://127.0.0.1:8000` (con ricerca automatica porta libera 8001, 8002...)
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

### Backup Transazionale, Ripristino & Migrazione Automatica
- **Backup Online Atomico**: Utilizzo dell'API nativa `sqlite3.Connection.backup()`, che copia il database senza rischio di lock o corruzione dati.
- **Archivio All-in-One**: Generazione di file `.zip` compressi contenenti l'intero database e tutti i documenti PDF dei preventivi.
- **Ripristino Sicuro (Disaster Recovery)**:
  - Caricamento diretto di archivi `.zip` dall'interfaccia o ripristino con 1 clic dallo storico.
  - Verifica automatica dell'integrità del database prima della sovrascrittura.
  - Generazione preventiva di una copia di sicurezza automatica pre-ripristino per azzerare qualsiasi rischio di perdita dati.
  - **Auto-Migrazione dello Schema**: Al ripristino di un backup proveniente da versioni precedenti, il sistema esegue in automatico le migrazioni DDL, garantendo piena compatibilità con qualsiasi nuova funzionalità aggiunta al gestionale.
- **Sincronizzazione Google Drive**: Supporto per l'upload automatico sul cloud via OAuth2 (posizionando le credenziali in `app/secrets/google_credentials.json`).

---

## Suite di Test Automatizzati

Il progetto include una suite di collaudo automatizzata con **`pytest`** che verifica la corretta esecuzione di:
- Calcoli matematici e fiscali del preventivo (`test_calculate_quote_breakdown`).
- Operazioni CRUD, cambio stato e duplicazione progressiva (`test_quote_crud_and_duplication`).
- Filtri di ricerca full-text e per stato (`test_list_quotes_filters`).
- Generazione conforme e validazione header PDF (`test_pdf_generation`).
- Backup locale transazionale SQLite (`test_backup_service`).
- Endpoint web e rendering template (`test_fastapi_endpoints`).
- Generazione PDF protetta da entità XML (`test_pdf_generation_with_xml_special_characters`).
- Modalità WAL del database e integrità indici (`test_database_wal_and_indexes`).
- Gestione codici di stato 404 per risorse mancanti (`test_404_error_handling`).
- Sanitizzazione parametri numerici negativi (`test_negative_input_sanitization`).
- Funzionalità di backup e ripristino sicuro (`test_backup_restore_functionality`).
- Endpoint web di upload e ripristino archivio (`test_backup_restore_endpoints`).

### Esecuzione della Suite

```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

Risultato atteso:
```text
======================= 12 passed in 0.40s ========================
```

---

## Struttura della Repository

```text
tenuta-turrita-quote-manager/
├── .github/workflows/
│   └── build-windows-exe.yml    # Pipeline CI/CD per compilazione automatica .exe
├── app/
│   ├── main.py                  # Router principale FastAPI, Lifespan e middleware
│   ├── db.py                    # Gestore connessione SQLite, inizializzazione schema
│   ├── paths.py                 # Risoluzione percorsi compatibile con .exe congelati
│   ├── services/
│   │   ├── quote_service.py     # Logica di business, modelli gastronomici e calcoli
│   │   ├── pdf_service.py       # Motore ReportLab luxury con NumberedCanvas
│   │   ├── email_service.py     # Client SMTP multipart (HTML + Text + PDF)
│   │   └── backup_service.py    # Backup transazionale SQLite e sync Google Drive
│   ├── static/
│   │   ├── style.css            # Fogli di stile istituzionali Tenuta Turrita
│   │   ├── app_icon.ico         # Icona desktop applicazione Windows
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
├── scripts/
│   └── setup_windows.ps1        # Auto-provisioning Python e dipendenze Windows 10/11
├── tests/
│   └── test_app.py              # Suite di test automatizzati pytest
├── desktop_app.py               # Entrypoint applicazione desktop (PyInstaller)
├── build_windows.py             # Script Python di compilazione .exe
├── avvia_windows.bat            # Launcher rapido per Windows 10/11 (con auto-setup)
├── compila_exe_windows.bat      # Script batch per compilare l'eseguibile su Windows
├── avvia_mac.command            # Launcher con doppio clic per macOS Finder
├── avvia_linux.sh               # Launcher con auto-rilevamento per distribuzioni Linux
├── run_local.py                 # Script di avvio con auto-rilevamento venv e porte
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
