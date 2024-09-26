from flask import render_template_string
from google.cloud import firestore, storage
import datetime

# Initialize firestore client
db = firestore.Client()
# Initialize google storage client
storage_client = storage.Client()

def home(request):
    data_selected = request.args.get('data')
    
    # If a date is picked, retrieve data in that day
    if data_selected:
        start = datetime.datetime.strptime(data_selected, "%Y-%m-%d")
        end = start + datetime.timedelta(days=1)
        sensorDB = db.collection('sensors').where('timestamp', '>=', start).where('timestamp', '<', end).stream()
    # If there is no date selected print last 100 values
    else:
        sensorDB = db.collection('sensors').order_by('timestamp').limit(100).stream()
    
    data = [['Time', 'Temperature', 'Consumption']]
    # Save data in dictionary
    for doc in sensorDB:
        dati = doc.to_dict()
        data.append([dati['timestamp'].strftime("%Y-%m-%d %H:%M:%S"), dati['temperature'], dati['consumption']])
    
    # Define HTML code
    html = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeGuard - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #2c2f33;
            background-image: url('https://images.unsplash.com/photo-1503264116251-35a269479413?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1950&q=80');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            height: 100vh;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        h1, h2, label {
            color: #ffffff;
        }
        .form-control {
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid #6c757d;
        }
        .form-control:focus {
            background-color: rgba(255, 255, 255, 0.2);
            box-shadow: none;
            border-color: #80bdff;
        }
        .btn-custom {
            background-color: #17a2b8;
            border: none;
            border-radius: 50px;
            padding: 10px 20px;
        }
        .btn-custom:hover {
            background-color: #138496;
        }
        .card-custom {
            background-color: rgba(0, 0, 0, 0.6);
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            padding: 20px;
        }
        .carousel-control-prev-icon, .carousel-control-next-icon {
            background-color: rgba(0, 0, 0, 0.5);
        }
        .carousel-item img {
            border-radius: 15px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row text-center">
            <div class="col-lg-12">
                <h1 class="mb-4">HomeGuard - Dashboard</h1>
            </div>
        </div>

        <!-- Form to pick date -->
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card-custom p-4 mb-4">
                    <form method="get" action="/website">
                        <label for="data" class="form-label">Seleziona una data:</label>
                        <input type="date" id="data" name="data" class="form-control mb-3" value="{{ data_selected }}">
                        <button type="submit" class="btn btn-custom">Visualizza</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Graph section -->
        <div class="row">
            <div class="col-lg-12">
                <h2 class="text-center mb-4">Grafico temperatura-consumi</h2>
                <div id="chart_div" style="width: 100%; height: 500px;" class="mx-auto"></div>
            </div>
        </div>

        <!-- Image section -->
        <div class="row justify-content-center mt-5">
            <div class="col-md-8">
                <h2 class="text-center mb-4">Immagini correlate</h2>
                <div id="slideshowContainer" class="carousel slide" data-bs-ride="carousel">
                    <div class="carousel-inner" id="slideshow"></div>
                    <button class="carousel-control-prev" type="button" data-bs-target="#slideshowContainer" data-bs-slide="prev" id="prev" style="visibility: hidden;">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="sr-only">Previous</span>
                    </button>
                    <button class="carousel-control-next" type="button" data-bs-target="#slideshowContainer" data-bs-slide="next" id="next" style="visibility: hidden;">
                        <span class="carousel-control-next-icon" aria-hidden="true"></span>
                        <span class="sr-only">Next</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.12.9/dist/umd/popper.min.js"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script type="text/javascript">
        google.charts.load('current', {'packages':['corechart']});
        google.charts.setOnLoadCallback(drawChart);

        // Function that create chart from data
        function drawChart() {
            var data = google.visualization.arrayToDataTable({{ chart_data|safe }});
            // Customize chart
            var options = {
                title: 'Dati sensori',
                hAxis: {title: 'Tempo', titleTextStyle: {color: '#333'}},
                vAxis: {minValue: 0, textStyle: {color: '#333'}},
                backgroundColor: '#bebebe',
                legendTextStyle: {color: '#333'},
                titleTextStyle: {color: '#333'},
                pointSize: 5,
                tooltip: { isHtml: true }
            };
            // Define chart as line chart
            var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
            chart.draw(data, options);
            // Add listener that fetch images in that day and then display them
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
                    // Perform GET request to another gfunction
                    url: "https://europe-west3-pcloud-pesole-2024.cloudfunctions.net/getImages",
                    method: "GET",
                    data: {timestamp: date},
                    success: function(response) {
                        // Extract URLs from images from object array
                        var imageUrls = response.map(function(imageObject) {
                        return imageObject.url;
                        });

                        // Call function that displays images from url
                        displayImages(imageUrls);
                    },
                    error: function(error) {
                        console.error("Errore nel recupero delle immagini", error);
                    }
                });
            }

            // Function that displays images from url
            function displayImages(images) {
                var slideshowDiv = document.getElementById('slideshow');
                slideshowDiv.innerHTML = '';
                // Initialize index
                var i = 0;
                // If there are no images in that day, hide the slideshow element
                if (images.length === 0) {
                    slideshowDiv.innerHTML = '<p>Nessuna immagine disponibile per questa data.</p>';
                    document.getElementById("prev").style.visibility = "hidden";
                    document.getElementById("next").style.visibility = "hidden";
                } else {
                    // For each image found in that day create a div for the image
                    images.forEach(function(image) {
                    var divElement = document.createElement('div');
                    divElement.classList.add('carousel-item');
                    // If it is first iteration, set the image as first
                    if (i== 0){
                        divElement.classList.add('active');
                    }
                    // Create image element with some styles
                    var imgElement = document.createElement('img');
                    imgElement.classList.add('d-block','w-100');
                    imgElement.src = image;
                    imgElement.style.width = '200px';
                    imgElement.style.margin = '5px';
                    divElement.appendChild(imgElement);
                    slideshowDiv.appendChild(divElement);
                    i++;
                });
                // After all, show buttons to slide images
                document.getElementById("prev").style.visibility = "visible";
                document.getElementById("next").style.visibility = "visible";
            }
        }
    </script>
</body>
</html>
""" # Paste here your HTML
    return render_template_string(html, chart_data=data, data_selected=data_selected)