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
        start = datetime.datetime.strptime(data_selected, "%Y-%m-%d")
        end = start + datetime.timedelta(days=1)
        sensorDB = db.collection('sensori').where('timestamp', '>=', start).where('timestamp', '<', end).stream()
    else:
        sensorDB = db.collection('sensori').order_by('timestamp').limit(100).stream()
    
    data = [['Time', 'Temperature', 'Consumption']]
    for doc in sensorDB:
        dati = doc.to_dict()
        data.append([dati['timestamp'].strftime("%Y-%m-%d %H:%M:%S"), dati['temperature'], dati['consumption']])
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Home Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.12.9/dist/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
        <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
        <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            body {
                background-color: #343a40;
                height: 100%;
                background-image: url('https://images.unsplash.com/photo-1503264116251-35a269479413?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1950&q=80');
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
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
                var i = 0;
                if (images.length === 0) {
                    slideshowDiv.innerHTML = '<p>Nessuna immagine disponibile per questa data.</p>';
                    document.getElementById("prev").style.visibility = "hidden";
                    document.getElementById("next").style.visibility = "hidden";
                } else {
                    images.forEach(function(image) {
                    var divElement = document.createElement('div');
                    divElement.classList.add('carousel-item');
                    if (i== 0){
                        divElement.classList.add('active');
                    }
                    var imgElement = document.createElement('img');
                    imgElement.classList.add('d-block','w-100');
                    imgElement.src = image;
                    imgElement.style.width = '200px';
                    imgElement.style.margin = '5px';
                    divElement.appendChild(imgElement);
                    slideshowDiv.appendChild(divElement);
                    i++;
                });
                document.getElementById("prev").style.visibility = "visible";
                document.getElementById("next").style.visibility = "visible";
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
        <div id="slideshowContainer" style="display: flex; width: 25%; margin: auto;" class="carousel slide" data-ride="carousel">
            <div class="carousel-inner" id="slideshow">
            </div>
            <a class="carousel-control-prev" href="#slideshowContainer" role="button" data-slide="prev" id="prev" style="visibility: hidden;">
                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                <span class="sr-only">Previous</span>
            </a>
            <a class="carousel-control-next" href="#slideshowContainer" role="button" data-slide="next" id="next" style="visibility: hidden;">
                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                <span class="sr-only">Next</span>
            </a>
        </div>
        <!-- <div id="slideshow" style="display: flex;"></div> -->
    </body>
    </html>
    """

    return render_template_string(html, chart_data=data, data_selected=data_selected)

if __name__ == "__main__":
    app.run(debug=True)