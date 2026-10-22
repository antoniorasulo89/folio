# Folio — La tua biblioteca, offline.

App desktop per raccogliere i tuoi libri scolastici in PDF. Scegli la piattaforma nella barra laterale, collega l’account e prepara il download dalla biblioteca. Evoluzione di ScaricaLibri.

Porting Python dei downloader di [Leone25](https://github.com/Leone25).

| Piattaforma | Login | Cosa serve |
|---|---|---|
| bSmart | email + password o cookie | selezionare il libro nella biblioteca |
| digibook24 | cookie del browser | accesso editore, poi cookie della sessione |
| Sanoma | email + password | selezionare il libro nella biblioteca |
| Zanichelli (BookTab + Kitaboo) | email + password | selezionare il libro nella biblioteca |
| HUB Scuola (Young + Kids) | email + password | selezionare il libro nella biblioteca |
| MyLim (Loescher) | email + password | selezionare il libro nella biblioteca |

## Scarica Folio

[Folio 3.1.0.dev5](https://github.com/antoniorasulo89/folio/releases/tag/v3.1.0-dev.5) corregge il catalogo Sanoma e permette di scaricare i suoi archivi grandi direttamente su disco. Verificato su un archivio reale da circa 3 GB, convertito in un PDF di 434 pagine. Include anche la precedente correzione della tastiera Windows con Bloc Num attivo.

| Sistema | Installa o aggiorna | Versione portabile | Architettura |
|---|---|---|---|
| Windows | **[Scarica installer .exe](https://github.com/antoniorasulo89/folio/releases/download/v3.1.0-dev.5/Folio-Windows-Setup.exe)** | [ZIP](https://github.com/antoniorasulo89/folio/releases/download/v3.1.0-dev.5/Folio-Windows.zip) | x86_64 |
| macOS | **[Scarica .dmg](https://github.com/antoniorasulo89/folio/releases/download/v3.1.0-dev.5/Folio-macOS.dmg)** | [ZIP](https://github.com/antoniorasulo89/folio/releases/download/v3.1.0-dev.5/Folio-macOS.zip) | Apple Silicon / ARM64 |
| Linux Debian/Ubuntu | **[Scarica .deb](https://github.com/antoniorasulo89/folio/releases/download/v3.1.0-dev.5/Folio-Linux-amd64.deb)** | [ZIP](https://github.com/antoniorasulo89/folio/releases/download/v3.1.0-dev.5/Folio-Linux.zip) | x86_64, glibc ≥ 2.39 |

Non serve installare Python. Gli eseguibili di sviluppo non sono firmati; l’app macOS non è notarizzata. Il pacchetto Linux è compilato su Ubuntu 24.04.

### Installazione e aggiornamento

- **Windows:** chiudi Folio ed esegui l’installer. Installa nel profilo utente e crea il collegamento nel menu Start; lo stesso installer aggiorna l’installazione precedente. Se usavi lo ZIP, passa all’installer e avvia Folio dal menu Start.
- **macOS:** apri il DMG e trascina `Folio.app` in `Applications`. Per aggiornare, chiudi Folio e sostituisci l’app precedente.
- **Linux Debian/Ubuntu:** dalla cartella del download esegui `sudo apt install ./Folio-Linux-amd64.deb`. Lo stesso comando aggiorna una versione già installata.
- **ZIP portabili:** estrai tutto lo ZIP in una cartella nuova e apri `Folio.exe`, `Folio.app` oppure `Folio`. Su Linux, se necessario: `chmod +x Folio`.

L’aggiornamento sostituisce l’applicazione; credenziali conservate nel portachiavi, indice della biblioteca e PDF scaricati restano nelle rispettive cartelle utente. Non è presente un aggiornamento automatico: per le versioni successive scarica ed esegui il nuovo pacchetto.

I pacchetti vengono compilati con GitHub Actions, con 60 controlli offline, prova di avvio GUI e verifica del contenuto installato. Su Windows viene provata anche la reinstallazione sullo stesso percorso. I checksum `.sha256` sono disponibili tra i file della release.

Questa versione precede gli esperimenti OCR: non include riconoscimento del testo, account salvati o libri scaricati.

Apri **Account e accessi** per configurare ogni piattaforma, poi premi **Collega e carica biblioteca**.
Il salvataggio è disattivato inizialmente: i dati restano solo in memoria.
Per conservarli, seleziona **Conserva le credenziali su questo dispositivo** e premi **Salva preferenze**.
Deselezionando l’opzione e salvando, rimuovi la copia persistente e mantieni i dati per la sessione.
Il portachiavi usa DPAPI su Windows, Keychain su macOS e Secret Service su Linux; senza un backend sicuro il salvataggio viene rifiutato.
**Rimuovi account e credenziali** rimuove i dati salvati e chiude la sessione. Le credenziali già salvate nel portachiavi sono riconosciute.
Durante accessi e download, il cambio di piattaforma e le operazioni duplicate sono bloccati.

## Come ottenere token manuali (solo se il login con credenziali non va)

- **HUB Scuola**: apri il libro nel lettore web, F12 → Rete, ricarica,
  clicca la richiesta con il Volume ID, copia `token-session`.
- **MyLim**: su mylim.loescher.it fai login, F12 → Applicazione →
  Archiviazione locale → copia `token`.
- **bSmart con Google/Microsoft**: F12 → Cookie → `_bsw_session_v1_production`
  (campo facoltativo nella schermata bSmart).

## Avvio da sorgente

```bash
pip install -r requirements.txt
python app_gui.py
```

## Creare l'eseguibile da soli

- Windows: doppio click su `build_exe.bat`
- Linux/macOS: `pip install -r requirements-build.txt`, poi `python scripts/package_ci.py Linux` oppure `python scripts/package_ci.py macOS`. Su Linux serve un display virtuale per la prova GUI.
- GitHub Actions: il workflow **Folio native packages** può essere avviato manualmente e compila i tre sistemi. Gli ZIP verificati sono disponibili negli artifact; la pubblicazione di una release è separata.

## Test

```bash
python test_all.py
python test_security.py
```

## Nota legale

Solo backup personale di libri acquistati. Verifica la normativa del tuo paese.
Attribuzioni e licenze dei componenti in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). La licenza MIT dei porting originali non equivale alla licenza dell’intero bundle, che include PyMuPDF/MuPDF.

## Identità visiva

Vedi [BRAND.md](BRAND.md) per il sistema visivo e i flussi della nuova interfaccia.

Le prossime build usano il nome **Folio** (`Folio-Windows.exe`, `Folio-Linux`, `Folio-macOS`); il servizio del portachiavi mantiene il nome precedente per compatibilità.

## Biblioteca locale

**Biblioteca** mostra i PDF scaricati che esistono ancora sul dispositivo, indipendentemente dall’account attivo. L’indice sopravvive ai riavvii e viene controllato aprendo la pagina, tornando all’app o premendo **Aggiorna**. I nuovi PDF nella cartella di destinazione vengono riconosciuti; per altri file già scaricati usa **Aggiungi PDF**. Un file spostato o eliminato scompare dalla lista; può essere aggiunto dalla nuova posizione. Ogni titolo offre **Apri PDF** e **Cartella**. **Nuovi download** contiene invece i titoli disponibili sulla piattaforma.


## Correzione tastiera (3.1.0.dev5)

Su Windows, il modificatore Tk `Command` collideva con il bit usato da Bloc Num: premere `a` selezionava tutto, `v` incollava e `c`/`x` potevano attivare copia/taglia. La correzione limita Command a macOS; le scorciatoie Ctrl e il menu contestuale restano disponibili. La regressione verifica minuscole e maiuscole nei campi email e password, con e senza Bloc Num.

## Affidabilità e sicurezza

- Nuovi account: conservazione soltanto con scelta esplicita. Account già conservati: checkbox coerente con il portachiavi. Errori di lettura/cifratura non cancellano l’archivio precedente; scritture atomiche e aggiornamenti protetti tra istanze.
- Windows DPAPI, macOS Keychain aggiornato senza cancellazione preventiva, Linux Secret Service. Il vecchio archivio Linux in chiaro viene segnalato nella pagina Account e può essere rimosso con un’azione esplicita; non viene riscritto in chiaro.
- Download incompleti, ZIP con percorsi non sicuri e risposte HTML al posto dei PDF vengono rifiutati. I PDF sono validati prima della pubblicazione. Download ripetuti ricevono un nome distinto; allegati pubblicati in una cartella nuova.
- SVG: normalizzazione JPEG incorporati, controllo delle immagini e supporto SVG compressi. Risorse mancanti interrompono la conversione.
- Annullamento e chiusura controllata; letture HTTP limitate, timeout, deadline di 15 minuti e tre tentativi per GET transitori. POST di accesso non ritentati automaticamente. La cancellazione durante una richiesta può attendere il timeout di rete.
- Biblioteca verificata in background, ricerca con breve ritardo e massimo 100 risultati mostrati per ricerca. Un indice corrotto viene conservato in una copia prima della ricostruzione.
- digibook24 usa il cookie dell’accesso editore nel browser; le sue password non vengono inviate al login bSmart.
- Dipendenze con versioni fissate e build isolata. `requirements-build.txt` include gli strumenti di compilazione e controllo. La CI esegue test e prova del bundle prima dell’upload; i pacchetti Windows, Linux e macOS sono stati compilati e verificati sui rispettivi runner.

La versione 3.1.0.dev5 è pubblicata come prerelease: i download sono disponibili in cima a questa pagina.

## Correzioni Sanoma (3.1.0.dev5)

Il catalogo viene letto dopo la sincronizzazione dei prodotti; i formati di risposta dei due endpoint vengono gestiti separatamente. Gli ZIP sono scaricati a blocchi su disco, con avanzamento in MB, annullamento e pubblicazione solo dopo un trasferimento completo. Limiti dedicati: 4 GiB per archivio trasferito e 8 GiB complessivi per i contenuti ZIP; restano i controlli su percorsi, collegamenti e singoli file. Le altre risposte HTTP mantengono il limite di 512 MiB. La conversione è SVG → PDF, senza OCR.
