# Restaurant Quote Manager

Webapp locale multipiattaforma per la gestione di preventivi ristorante/eventi.

## Funzioni incluse nell'MVP

- Numerazione progressiva preventivi: `ANNO-0001`, `ANNO-0002`, ecc.
- Anagrafica cliente.
- Tipologia evento: Matrimonio, Cresima, Battesimo, Compleanno, Laurea, Generico.
- Menù con portate multiple e piatti multipli.
- Note per preventivo e per singolo piatto.
- Prezzi per adulti/bambini, extra, sconto, IVA e totale calcolato.
- Stato preventivo: bozza, inviato, in attesa, accettato, rifiutato, scaduto, annullato.
- Formula contrattuale con IBAN, caparra confirmatoria, date di conferma, saldo e penali.
- Generazione PDF A4.
- Stampa da browser.
- Invio email SMTP con PDF allegato.
- Backup locale in ZIP.
- Backup Google Drive predisposto tramite OAuth e scope `drive.file`.
- Impostazioni azienda, SMTP e staff.

## Avvio rapido

```bash
cd restaurant_quote_manager
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Poi apri:

```text
http://127.0.0.1:8000
```

## Backup Google Drive

Il backup locale funziona subito. Per abilitare Google Drive:

1. Crea un progetto su Google Cloud.
2. Abilita Google Drive API.
3. Crea credenziali OAuth Client Desktop.
4. Scarica il file JSON e rinominalo in:

```text
app/secrets/google_credentials.json
```

5. Vai nella webapp in **Backup** e clicca su **Crea backup**.
6. Al primo uso verrà aperto il flusso OAuth locale e salvato il token in `data/google_token.json`.

Scope usato: `https://www.googleapis.com/auth/drive.file`.

## Note importanti

Questa è una base MVP funzionante. Prima di usarla in produzione conviene aggiungere:

- login utenti;
- cifratura password SMTP;
- firma grafometrica semplice;
- template PDF personalizzabile da interfaccia;
- ruoli utente;
- audit log avanzato;
- validazione legale della formula contrattuale.
