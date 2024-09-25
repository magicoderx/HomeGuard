google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);
// Function that create chart from data
function drawChart() {
    var data = google.visualization.arrayToDataTable(chartData);
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
            // Perform GET request to another function
            url: "/getImages",
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