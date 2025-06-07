# Sold By Romo - Gestione Inventario

Applicazione web per la gestione dell'inventario, acquisti e vendite di un negozio.

## Requisiti

- Docker
- Docker Compose

## Installazione su Mac

1. Installare Docker Desktop per Mac:
   - Scarica Docker Desktop dal sito ufficiale [docker.com](https://www.docker.com/products/docker-desktop)
   - Segui le istruzioni di installazione
   - Avvia Docker Desktop

2. Clona o scarica questo repository sul tuo Mac

## Esecuzione dell'applicazione

1. Apri il Terminal
2. Naviga nella cartella del progetto:
   ```
   cd percorso/alla/cartella/Mercato_Romo
   ```
3. Avvia l'applicazione con Docker Compose:
   ```
   docker-compose up
   ```
4. Apri un browser e visita:
   ```
   http://localhost:5000
   ```

Per arrestare l'applicazione:
- Premi `Ctrl+C` nel Terminal
- Oppure esegui `docker-compose down` da un altro Terminal

## Dati e database

Il database SQLite (`sold_by_romo.db`) è configurato come volume di Docker, quindi:
- I dati persisteranno tra i riavvii del container
- Qualsiasi modifica ai dati (nuovi articoli, acquisti, vendite) sarà salvata sul tuo computer

## Funzionalità

- Gestione inventario: aggiungere, modificare e cercare articoli
- Registrazione acquisti: registrare nuovi acquisti con aggiornamento automatico dell'inventario
- Registrazione vendite: registrare le vendite con controllo del livello di inventario
- Statistiche: visualizzare statistiche di vendita, profitti e articoli più venduti

## Supporto

In caso di problemi con l'applicazione, assicurarsi che:
1. Docker Desktop stia funzionando correttamente (l'icona nella barra di stato dovrebbe essere verde)
2. La porta 5000 non sia utilizzata da altre applicazioni sul Mac
