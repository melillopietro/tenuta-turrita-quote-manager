# Tenuta Turrita Quote Manager

Gestionale web per la creazione, gestione, personalizzazione e invio di preventivi per eventi, matrimoni, cerimonie e ricevimenti.

Il progetto nasce come **Restaurant Quote Manager**, ma è stato successivamente personalizzato per **Tenuta Turrita**, con branding dedicato, colori coordinati, logo, gestione clienti multipli, menù adulti/bambini, PDF personalizzati, condizioni contrattuali e funzioni avanzate di gestione preventivi.

---

## Indice

- [Funzionalità principali](#funzionalità-principali)
- [Personalizzazione Tenuta Turrita](#personalizzazione-tenuta-turrita)
- [Gestione clienti](#gestione-clienti)
- [Menù adulti e menù bambini](#menù-adulti-e-menù-bambini)
- [PDF preventivo](#pdf-preventivo)
- [Contratto e condizioni](#contratto-e-condizioni)
- [Invio email](#invio-email)
- [Backup](#backup)
- [Stack tecnico](#stack-tecnico)
- [Struttura progetto](#struttura-progetto)
- [Installazione](#installazione)
- [Primo avvio](#primo-avvio)
- [Configurazione iniziale](#configurazione-iniziale)
- [Flusso operativo consigliato](#flusso-operativo-consigliato)
- [Comandi utili](#comandi-utili)
- [File da non caricare su GitHub](#file-da-non-caricare-su-github)
- [Note di sicurezza](#note-di-sicurezza)
- [Stato attuale](#stato-attuale)
- [Licenza](#licenza)

---

## Funzionalità principali

Il sistema consente di:

- creare nuovi preventivi;
- visualizzare l’elenco dei preventivi;
- aprire il dettaglio di un preventivo;
- modificare preventivi esistenti;
- duplicare un preventivo esistente;
- eliminare preventivi;
- aggiornare lo stato del preventivo;
- generare PDF;
- inviare il preventivo via email;
- gestire contratti e condizioni di conferma;
- gestire backup locali ed eventualmente Google Drive.

Gli stati previsti sono:

- `bozza`
- `inviato`
- `in_attesa`
- `accettato`
- `rifiutato`
- `scaduto`
- `annullato`

---

## Personalizzazione Tenuta Turrita

Il software è stato brandizzato per **Tenuta Turrita**, con:

- nome struttura aggiornato;
- payoff: `Villa per matrimoni ed eventi`;
- logo personalizzato;
- palette colori coordinata;
- layout laterale personalizzato;
- PDF brandizzato;
- stampa preventivo con intestazione Tenuta Turrita;
- condizioni contrattuali standard;
- dati struttura configurabili da impostazioni.

### Palette colori

| Elemento | Colore |
|---|---|
| Verde salvia principale | `#87977A` |
| Verde scuro | `#6F8062` |
| Oro caldo | `#DDBA74` |
| Oro chiaro | `#E8C98D` |
| Sfondo elegante | `#F6F3EC` |
| Testo principale | `#2F352C` |
| Testo secondario | `#6C7367` |

---

## Gestione clienti

Il preventivo supporta la gestione di più intestatari, utile soprattutto per matrimoni o eventi familiari.

### Primo cliente

Per il primo cliente sono presenti:

- ruolo;
- nome;
- cognome;
- telefono;
- email;
- codice fiscale / partita IVA;
- indirizzo;
- note cliente.

Ruoli disponibili:

- Non indicato;
- Sposo;
- Sposa;
- Cliente principale;
- Referente evento.

### Secondo cliente / sposo / sposa

È stata aggiunta una sezione dedicata per un secondo cliente.

Campi disponibili:

- ruolo;
- nome;
- cognome;
- telefono;
- email.

Ruoli disponibili:

- Non indicato;
- Sposo;
- Sposa;
- Secondo cliente;
- Referente evento.

Nel PDF e nella stampa il preventivo può quindi essere intestato, ad esempio, a:

```text
Sposo: Mario Rossi e Sposa: Anna Bianchi
```

---

## Menù adulti e menù bambini

Il sistema distingue tra:

- menù adulti;
- menù bambini.

### Menù adulti

Il menù adulti prevede portate come:

- buffet di benvenuto;
- aperitivo;
- antipasto;
- primo;
- secondo;
- frutta;
- dolci;
- portata personalizzata.

### Menù bambini

È stata aggiunta una sezione dedicata al menù bambini, con una struttura tipica composta da:

- antipasto;
- primo;
- secondo.

Ogni voce menù può includere:

- portata;
- nome piatto;
- descrizione;
- allergeni;
- note;
- eventuale extra economico.

Nel PDF i piatti bambini vengono evidenziati come:

```text
Menù bambini - Antipasto
Menù bambini - Primo
Menù bambini - Secondo
```

---

## PDF preventivo

Il PDF generato include:

- logo/stile Tenuta Turrita;
- nome struttura;
- payoff;
- dati di contatto;
- numero preventivo;
- dati cliente;
- dati evento;
- menù proposto;
- menù bambini, se presente;
- riepilogo economico;
- note;
- condizioni contrattuali;
- spazio firma cliente;
- spazio firma struttura.

Il PDF viene generato tramite **ReportLab**.

---

## Contratto e condizioni

Il sistema supporta la gestione delle condizioni di conferma del preventivo.

Le condizioni standard includono:

- validità del preventivo;
- modalità di conferma;
- acconto/caparra;
- conferma numero invitati;
- saldo;
- modifiche organizzative;
- eventuali penali o condizioni di annullamento.

Le condizioni possono essere inserite nel contratto del singolo preventivo e riportate nel PDF.

---

## Invio email

Il sistema consente l’invio del preventivo via email con PDF allegato.

La configurazione SMTP è gestibile dalla pagina **Impostazioni**.

Campi principali:

- host SMTP;
- porta;
- SSL;
- username;
- password;
- nome mittente;
- email mittente.

---

## Backup

Il software include una sezione backup.

Sono previsti:

- backup locali;
- eventuale integrazione Google Drive tramite file OAuth;
- cartella dedicata per i backup.

Per abilitare Google Drive è necessario inserire il file:

```text
app/secrets/google_credentials.json
```

La cartella `app/secrets/` non deve essere caricata su GitHub.

---

## Stack tecnico

Il progetto utilizza:

- Python 3;
- FastAPI;
- Uvicorn;
- Jinja2 Templates;
- SQLite;
- ReportLab;
- HTML/CSS/JavaScript vanilla.

---

## Struttura progetto

```text
restaurant_quote_manager/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── services/
│   │   ├── backup_service.py
│   │   ├── email_service.py
│   │   ├── pdf_service.py
│   │   └── quote_service.py
│   ├── static/
│   │   ├── style.css
│   │   ├── tenuta_turrita_logo.png
│   │   └── tenuta_turrita_logo.svg
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── quotes.html
│   │   ├── quote_form.html
│   │   ├── quote_edit.html
│   │   ├── quote_detail.html
│   │   ├── quote_print.html
│   │   ├── contract_form.html
│   │   ├── send_form.html
│   │   ├── settings.html
│   │   └── backup.html
│   └── secrets/
│       └── .gitkeep
├── data/
│   ├── .gitkeep
│   ├── pdfs/
│   │   └── .gitkeep
│   └── backups/
│       └── .gitkeep
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Installazione

### 1. Clonare il repository

```bash
git clone https://github.com/USERNAME/tenuta-turrita-quote-manager.git
cd tenuta-turrita-quote-manager
```

Sostituire `USERNAME` con il proprio username GitHub.

---

### 2. Creare ambiente virtuale

Su Linux/Ubuntu:

```bash
python3 -m venv .venv
```

Attivare l’ambiente:

```bash
source .venv/bin/activate
```

---

### 3. Installare dipendenze

```bash
pip install -r requirements.txt
```

---

### 4. Avviare il software

Metodo consigliato:

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

In alternativa, se l’ambiente virtuale è attivo:

```bash
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

---

### 5. Aprire il browser

```text
http://127.0.0.1:8001
```

Documentazione API FastAPI:

```text
http://127.0.0.1:8001/docs
```

---

## Primo avvio

Al primo avvio il sistema crea automaticamente:

- database SQLite locale;
- tabelle principali;
- cartelle dati;
- impostazioni base;
- utente/staff di default.

Il database locale viene creato in:

```text
data/restaurant_quotes.db
```

Questo file non deve essere caricato su GitHub.

---

## Configurazione iniziale

Dopo il primo avvio, andare in:

```text
http://127.0.0.1:8001/settings
```

Configurare:

- nome struttura;
- email;
- telefono;
- indirizzo;
- IBAN;
- intestatario conto;
- SMTP;
- eventuale backup Google Drive;
- personale / compilatori menù.

Valori consigliati per Tenuta Turrita:

```text
Nome struttura: Tenuta Turrita
Payoff: Villa per matrimoni ed eventi
Indirizzo: Via Roma, Dragoni (CE)
Intestatario conto: Tenuta Turrita
```

---

## Flusso operativo consigliato

### Creare un preventivo

1. Aprire `Nuovo preventivo`.
2. Inserire dati cliente.
3. Inserire eventuale secondo cliente/sposo/sposa.
4. Inserire dati evento.
5. Compilare menù adulti.
6. Compilare menù bambini, se previsto.
7. Inserire riepilogo economico.
8. Salvare.

### Gestire un preventivo

Dalla pagina `Preventivi` è possibile:

- aprire il dettaglio;
- modificare;
- duplicare;
- eliminare.

### Generare PDF

Dal dettaglio del preventivo:

```text
PDF
```

### Inviare email

Dal dettaglio del preventivo:

```text
Invia email
```

---

## Comandi utili

### Avvio server

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Pulizia cache Python

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### Stato Git

```bash
git status
```

### Commit modifiche

```bash
git add .
git commit -m "Update Tenuta Turrita quote manager"
```

### Push su GitHub

```bash
git push
```

---

## File da non caricare su GitHub

Il file `.gitignore` deve escludere:

```text
.venv/
__pycache__/
*.pyc
data/*.db
data/*.db.*
data/pdfs/*
data/backups/*
.env
app/secrets/*
*.bak
*.bak_*
patch_*.py
app/static/*.pdf
app/static/*.zip
```

Devono invece rimanere tracciati:

```text
data/.gitkeep
data/pdfs/.gitkeep
data/backups/.gitkeep
app/secrets/.gitkeep
```

---

## Note di sicurezza

Questo software è pensato per uso locale o interno.

Prima di esporlo su Internet è necessario aggiungere:

- autenticazione;
- gestione utenti;
- autorizzazioni;
- protezione CSRF;
- hardening dei segreti;
- logging applicativo;
- HTTPS;
- backup sicuro;
- gestione errori avanzata.

Non caricare mai su GitHub:

- database reali;
- preventivi PDF;
- password SMTP;
- file OAuth Google;
- backup;
- dati personali dei clienti.

---

## Stato attuale

Funzionalità implementate:

- branding Tenuta Turrita;
- logo e colori personalizzati;
- dashboard personalizzata;
- gestione preventivi;
- modifica preventivo;
- eliminazione preventivo;
- duplicazione preventivo;
- gestione primo e secondo cliente;
- ruolo cliente;
- menù adulti;
- menù bambini;
- PDF brandizzato;
- condizioni contrattuali;
- invio email;
- backup locale/Google Drive;
- `.gitignore` per evitare caricamento dati sensibili.

---

## GitHub

Repository:

```text
https://github.com/melillopietro/tenuta-turrita-quote-manager
```

Dopo ogni modifica:

```bash
git add .
git commit -m "Descrizione modifica"
git push
```

---

## Licenza

Progetto interno sviluppato per la gestione preventivi di Tenuta Turrita.

Uso, distribuzione e modifica sono riservati al proprietario del repository.
