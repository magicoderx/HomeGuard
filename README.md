# HomeGuard
## Introduzione
Il seguente progetto tratta di una simulazione di sensori e videocamere di sorveglianza all'interno di una smart home. In particolare i sensori rilevano le temperature minuto per minuto insieme a consumo elettrico in quel lasso di tempo; mentre le videocamere di sorveglianza inviano foto, anch'esse una al minuto, che vengono poi elaborati da un'intelligenza artificiale che permette di rilevare il numero di volti all'interno dell'immagine. Il tutto viene visualizzato in un'interfaccia web attraverso grafici e slideshow.

Il motore per far funzionare tutto è **Google Cloud**, in particolare con l'ausilio delle **Google Cloud Functions** per gestire le richieste e le risposte attraverso API REST. Vengono utilizzati anche i servizi di **Google Storage** per la memorizzazione della immagini e **Google Firestore** per il database (non relazionale) che conterrà i valori dei consumi e delle temperature.

## Strategia
L'idea principale per utilizzare le API REST è quella di utilizzare delle funzioni scirtte in python per ogni Cloud Function in ascolto sulla rispettiva URL fornita da Google. Diventa importante, essendo pubblico su internet, limitare gli accessi a Google Firestore e Cloud Functions per inibire accessi non desiderati. La stessa sicurezza va applicata alle immagini contenute in Google Storage, che dovranno essere accessibili soltanto alle opportune Google Functions. 

## Clients
In questo progetto, i codici python che dovranno girare sui client, simuleranno dei sensori e delle videocamere in una smart home. I client dovranno essere connessi ad internet in quanto dovranno inviare messaggi tramite protocollo HTTP. Per poter eseguire gli script è necessario eseguire questo comando sulla propria macchina:

```
pip install -r requirements.txt
```

In modo tale da installare tutte le dipendenze necessarie. Inoltre bisogna creare un file *.env* contenente i seguenti valori:

```
GFUNCTION_URL=<URL_GENERICO_DELLE_GFUNCTION>
```

### Generatore dati
Questo programma va in ciclo permanente (`while True`) con un timeout di 60 secondi. Ad ogni iterazione viene generato un valore casuale per la temperatura, supponendo un intervallo che va dai 19° ai 32° Celsius; poi viene generato un valore casuale per il consumo dell'energia misurato in kWh supponendo un valore decimale che va da 0 ad un massimo di 3. Nel caso dei consumi si genera un valore intero ed uno decimale che vengono sommati tra loro in modo da avere più dati differenti e, nel caso il valore intero sia 3 (il massimo previsto), si imposta il valore massimo a 3.0 proprio per evitare di eccedere con la somma dei decimali. Infine vengono inviati questi dati in formato JSON alla Cloud Function */getData* avendo conferma dell'esito.
### Fotocamera
Anche questa simulazione di videocamera di sorveglianza va in ciclo in modo permanente con timeout di 60 secondi. Ad ogni iterazione Crea un oggetto per acquisire i fotogrammi (il parametro `0` rappresenta la webcam predefinita del PC). Una volta acquisito il fotogramma lo si invia tramite una richiesta POST alla Cloud Function opportuna attendendo la risposta.

## Servers
I server in questo progetto non sono altro che Cloud Functions su cui sono definite delle funzioni. Per eseguire correttamente le varie funzioni per questo progetto bisogna impostare le opportune IAM per cui: l'entità *gfunction* deve avere i permessi di lettura/scrittura per Google Storage e Vertex AI che serviranno in alcune funzioni. Le entry point delle funzioni hanno come parametro `request` che ottiene, appunto, la richiesta che viene fatta dal client. Inoltre non sono necessarie le *credentials.json* in quanto si suppone che girino sotto lo stesso account di Google Cloud.

### Elaboratore dati
Per deployare questa funzione bisogna eseguire questo comando:
```
gcloud functions deploy getData \
  --runtime python312 \
  --region europe-west3 \
  --entry-point save_data \
  --trigger-http \
  --allow-unauthenticated
```
Questa funzione prende la richiesta parsata in JSON e ottiene i valori di `temperature` e `consumption` che aggiunge successivamente alla collection `sensors` di Google Firestore aggiungendo anche un valore relativo al timestamp che servirà per visualizzare in ordine le temperature sul grafico.

### Analizzatore immagini
Per deployare questa funzione bisogna eseguire il seguente comando:
```
gcloud functions deploy faceDetect \
  --runtime python312 \
  --region europe-west3 \
  --entry-point analyze_and_upload \
  --trigger-http \
  --allow-unauthenticated \
  --memory 1GB \
  --cpu 0.583 \
  --timeout 104s \
  --set-env-vars GFUNCTION_URL="URL_GENERICO_DELLE_GFUNCTION" \
  --set-env-vars GSTORAGE_ID="ID_GOOGLE_STORAGE" \
  --set-env-vars SMTP_SERVER="SERVER_SMTP_MAIL" \
  --set-env-vars SMTP_PORT="PORTA_SMTP" \
  --set-env-vars SMTP_LOGIN_USER="LOGIN_USER_SMTP" \
  --set-env-vars SMTP_LOGIN_PASS="LOGIN_PASSWORD_SMTP" \
  --set-env-vars SMTP_TO="DESTINATARIO_EMAIL"
```
Per questa applicazione c'è bisogno di più memoria e timeout rispetto alle altre Google Functions in quanto la ricezione di immagini e la loro elaborazione richiede più capacità di calcolo. Questa funzione ottiene e memorizza il file in una posizione temporanea nel container (salvando l'immagine anche in Google Storage con l'opportuna estensione) per poi analizzare l'immagine tramite il pacchetto `vertexai` chiedendo all'intelligenza artificiale qual'è il numero di volti che rileva, forzando una risposta numerica e senza punteggiatura in modo tale da poterla elaborare e parsare in intero.

Se l'intelligenza artificiale rileva 2 o più volti, la funzione invia una mail utilizzando i parametri forniti nelle variabili d'ambiente e utilizzando un template HTML ben formattato con il numero di volti e il link per visualizzare l'immagine in questione.

#### Criticità
Durante lo sviluppo di questa funzione sono sorti degli ostacoli riguardanti:
- L'utilizzo dell'immagine, in quanto si riscontravano errori nel recupero del file e per questo motivo è stato scelto di salvarla in una posizione temporanea nel container.
- Invio mail, in quanto utilizzando un server mail personalizzato si ottenevano degli errori di connessione. Si è optato per l'utilizzo di outlook come server di invio ma si incorreva in errori di autenticazione nonostante le credenziali corrette. Infine si è scelto di utilizzare l'SMTP di Google Gmail utilizzando la password per applicazioni e, inviando la mail a se stessi, non si riscontrano errori.

### Ottenitore di immagini
Per deployare questa funzione bisogna eseguire questo comando:
```
gcloud functions deploy getImages \
  --runtime python312 \
  --region europe-west3 \
  --entry-point get_images \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GSTORAGE_ID="ID_GOOGLE_STORAGE" \
  --service-account "SERVICE_ACCOUNT_ID"
```
Questa funzione funge da middleware per */website*. Ottiene il valore del timestamp dalla request e lo parsa nel formato di timestamp che si ottiene da `blob.time_created.date()`, in modo tale da poter ottenere tutti i file all'interno del Google Storage e inserire in un array, soltanto i file di quella data. Dopo aver creato questo array, viene creato un dizionario con le chiavi *name* e *url* utilizzato per inviare una risposta in JSON. In particolare l'URL fornito è un URL firmato in modo tale da poter fornire URL temporanei alla pagina web in modo tale da poter visualizzare correttamente le immagini nonostante sia inibito l'accesso dall'esterno.

#### Impostazione ruolo
Come si può notare dalla stringa di deploy, c'è un parametro `--service-account` che permette di specificare il service account che possiede la funzione. In questo caso il service account dovrà essere creato dal pannello `Google Cloud->IAM & Administration->Service Account`. Dopodiché si crea un service account che abbia un ruolo per viasualizzare gli elementi nello storage. A questo punto diventa necessario andare a creare una chiave privata per questo service account appena creato andando in `CHIAVI->Aggiungi chiave` per esportarla in formato JSON e caricarla nella stessa directory della funzione. In questo modo, quando verrà chiamata la funzione, questa accederà allo storage autenticandosi tramite credenziali e ciò permetterà di generare un URL temporaneo per le immagini

### Pagina web
Per deployare questa funzione bisogna eseguire questo comando:
```
gcloud functions deploy website \
  --runtime python312 \
  --region europe-west3 \
  --entry-point home \
  --trigger-http \
  --allow-unauthenticated
```
Questa funzione è il cuore del progetto che si occupa di mostrare a video una pagina in HTML. Dunque viene utilizzato il pacchetto Flask per renderizzare la pagina web. La richiesta alla funzione può essere: 
- Vuota, in questo caso si fa una query al firestore sugli ultimi 100 valori
- Un timestamp, in questo caso si fa una query al firestore sui valori memorizzati in quella data
Dopo aver ottenuto i risultati li si inserisce in un dizionario per poi passarli all'HTML che li elaborerà e li utilizzerà per mostrare a video il grafico. L'HTML in questo caso va inserito in una variabile come stringa in modo tale che Flask possa renderizzare l'HTML senza andare a ricercare il file nel folder *templates*

#### Dasboard HTML
Il file HTML in questione contiene al suo interno lo stile CSS e gli script in JavaScript per evitare di andare a ricercare file all'interno del sistema del container. È stato utilizzato Bootstrap 5.0 per una grafica moderna e gradevole esteticamente. L'interfaccia si divide in 3 sezioni:
- La scelta della data
- Il grafico delle temperature e consumi
- Lo slideshow delle immagini
Alla prima richiesta HTTP si chiama la funzione `drawChart()` che, appunto, disegna il grafico delle temperature e dei consumi attraverso la funzione `google.visualization.arrayToDataTable()` che fa parte delle Google Charts APIs e trasforma l'array creato dalla Cloud Function in un formato di tabella di dati (in particolare con `safe` non viene fatto ecaping dei caratteri, quindi il testo non viene trasformato). È stata creata una variabile contenente le opzioni per per personalizzare il grafico con colori e stili custom che è stata data poi in pasto alla funzione `google.visualization.LineChart(document.getElementById('chart_div')).draw()` per creare un grafico a linee. Su questo grafico è stata creata un funzione per cui, cliccando su un valore, il sistema ottiene le immagini di quella giornata e le mostra a video in uno slideshow; questo viene eseguito tramite una funzione AJAX che fa una richiesta GET alla Cloud Function per ottenere le immagini e chiama a sua volta un'altra funzione che crea tanti DIV elements quante sono le immagini in questione per andarli ad inserire nello slideshow
## Conclusioni
L'applicazione permette di non dover creare diversi IAM per gestire le varie funzioni, ma soltanto di una policy che permette l'accesso delle Cloud Functions alle rispettive risorse sul cloud.

Nonostante l'applicazione sia funzionante sono sorte delle problematiche soprattutto relative alla creazione della Cloud Function del sito web in quanto non compatibile con il container "blackbox" creato dalla Function stessa. Pertanto viene proposta una soluzione alternativa utilizzando Google Artifact Registry che permette di deployare delle immagini docker personalizzate che vengono poi gestite in Google Cloud Run. In questo caso il codice python è una vera e propria Flask application con tanto di rotte (andando a limitare il numero di Cloud Functions in quanto la funzione per ottenere le immagini non diventa altro che una rotta all'interno dell'applicazione). Così facendo si può anche gestire meglio la divisione degli stili e degli script in apposite cartelle, che vengono quindi nascoste dall'HTML.
Per deployare l'applicazione in questa modalità basterà buildare il Dockerfile con il seguente comando:
```
docker build -t gcr.io/<ID_PROGETTO>/flask-app:latest .
```
Una volta buildata l'immagine la si copia nel repository in cloud (Google Artifact Registry) tramite il seguente comando:
```
docker push gcr.io/<ID_PROGETTO>/flask-app:latest
```
E infine si avvia l'immagine creando appunto il container con l'eseguibile funzionante:
```
gcloud run deploy flask-app --image gcr.io/<ID_PROGETTO>/flask-app:latest --platform managed --region <REGIONE> --allow-unauthenticated
``` 
Per poi raggiungere il sito attraverso l'URL fornito da Google Cloud Run

Infine degli sviluppi futuri che sono stati presi in considerazione possono essere:
- Introduzione di nuovi sensori
- Creazione di un accesso tramite login al sito web
- Inserimento, attraverso una dashboard specifica, di una diversa abitazione con altri sensori
