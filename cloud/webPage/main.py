from flask import Flask, render_template_string, request, jsonify
from google.cloud import firestore, storage
import datetime

app = Flask(__name__)
db = firestore.Client()
storage_client = storage.Client()

@app.route("/", methods=["GET"])
def home(request):
    data_selected = request.args.get('data')
    
    if data_selected:
        # Parse date in gcloud format
        start = datetime.datetime.strptime(data_selected, "%Y-%m-%d")
        end = start + datetime.timedelta(days=1)
        # Get sensors data
        sensorDB = db.collection('sensori').where('timestamp', '>=', start).where('timestamp', '<', end).stream()
    else:
        sensorDB = db.collection('sensori').order_by('timestamp').limit(100).stream()
    
    data = [['Time', 'Temperature', 'Consumption']]
    for doc in sensorDB:
        dati = doc.to_dict()
        data.append([dati['timestamp'].strftime("%Y-%m-%d %H:%M:%S"), dati['temperature'], dati['consumption']])
    
    # Write HTML string
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Home Dashboard</title>
        <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
        <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            body {
                background-color: #343a40;
                height: 100vh;
                background-image: url('https://images.unsplash.com/photo-1503264116251-35a269479413?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1950&q=80');
                background-size: cover;
                background-position: center;
                color: #ffffff;
            }
            p,h1,h2,label {
                color: #ffffff !important
                }
        </style>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script type="text/javascript">
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            
            function drawChart() {
                var data = google.visualization.arrayToDataTable({{ chart_data|safe }});

                var options = {
                    title: 'Dati sensors',
                    hAxis: {title: 'Tempo', titleTextStyle: {color: '#333'}},
                    vAxis: {minValue: 0},
                    pointSize: 5,
                    tooltip: { isHtml: true }
                };

                var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
                chart.draw(data, options);

                google.visualization.events.addListener(chart, 'select', function() {
                    var selection = chart.getSelection();
                    if (selection.length > 0) {
                        var row = selection[0].row;
                        var date = data.getValue(row, 0);
                        fetchImages(date);
                    }
                });
            }

            function fetchImages(date) {
                $.ajax({
                    url: "https://europe-west3-pcloud-pesole-2024.cloudfunctions.net/getImages",
                    method: "GET",
                    data: {timestamp: date},
                    success: function(response) {
                        console.log(response)
                        // Estrarre gli URL delle immagini dall'array di oggetti
                        var imageUrls = response.map(function(imageObject) {
                        return imageObject.url;
                        });

                        // Chiamare displayImages con l'array di URL
                        displayImages(imageUrls);
                    },
                    error: function(error) {
                        console.error("Errore nel recupero delle immagini", error);
                    }
                });
            }

            function displayImages(images) {
                var slideshowDiv = document.getElementById('slideshow');
                slideshowDiv.innerHTML = '';
                if (images.length === 0) {
                    slideshowDiv.innerHTML = '<p>Nessuna immagine disponibile per questa data.</p>';
                } else {
                    images.forEach(function(image) {
                    var imgElement = document.createElement('img');
                    imgElement.src = image;
                    imgElement.style.width = '200px';
                    imgElement.style.margin = '5px';
                    slideshowDiv.appendChild(imgElement);
                });
            }
            }
        </script>
    </head>
    <body>
        <h1 class="mt-4 text-center">Dashboard</h1>
        <form method="get" action="/website">
            <label for="data">Seleziona una data:</label>
            <input type="date" id="data" name="data" value="{{ data_selected }}">
            <button type="submit">Visualizza</button>
        </form>
        
        <h2 class="mt-2">Grafico temperatura-consumi</h2>
        <div id="chart_div" style="width: 900px; height: 500px; margin: auto; padding-top:10px">
        </div>
        
        <h2 class="mt-2">Immagini correlate</h2>
        <div id="slideshow" style="display: flex;"></div>
    </body>
    </html>
    """

    return render_template_string(html, chart_data=data, data_selected=data_selected)

if __name__ == "__main__":
    app.run(debug=True)