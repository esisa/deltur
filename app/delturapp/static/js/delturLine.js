var delturLine = function () {

    //this.someProperty = 5;  //public

    var startIcon = L.AwesomeMarkers.icon({
      prefix: 'fa',
      icon: 'play', 
      markerColor: 'green'
    });
    
    var endIcon = L.AwesomeMarkers.icon({
      prefix: 'fa',
      icon: 'stop', 
      markerColor: 'red'
    });

    var id;
    var title;
    var description;
    var status = 0;

    var style = {
    	"width": 5,
    	"color": "#ff7800",
    	"opacity": 0.65,
    	"endIcon": false,
    	"startIcon": true,
    	"popup": false,
    	"label": {
    		"static": false,
    		"text": ""
    	}
    }

    this.init = function (_url) {  //public

        var fpfile = {url: _url, filename: 'hello.txt', mimetype: 'text/plain', isWriteable: false, size: 100};
        filepicker.read(fpfile, function(data){

	        //Upload to deltur.no/del/gpx
	        $.ajax({
	          type: "POST",
	          url: "/del/gpx",
	          data: data,
	          success: function (response) {
	                id = response.id;
	                status = 1; // File is uploaded

	                // Update style from server
	                downloadStyle();
	            },
	            error: function (response) {
	              status = -1; // Error in uploaded file
	            },
	          contentType: "application/gpx+xml",
	          dataType: "json"
	        });
            
        }); // END FILEPICKER
    };

    this.getId = function () {  //public
        return id;
    };

    this.getStatus = function () {  //public
        return status;
    };

    this.getTitle = function () {  //public
        return title;
    };
    this.setTitle = function (_title) {  //public
        title = _title;
    };

    this.getDescription = function () {  //public
         return description;
    };
    this.setDescription = function (_description) {  //public
        description = _description;
    };

    this.getStyle = function () {  //public
        return style;
    };

    this.setStyle = function (_style) {  //public

    	// Check if _style is valid??
        style = _style;
        uploadStyle();
    };

    this.renderToMap = function (_map) {  //public

    	var lineStyle = {
            "color": style.color,
            "weight": style.width,
            "opacity": style.opacity
        };

        // Get GeoJSON and add to map
    	$.getJSON('/'+id+'/geojson', function (data) {
    		geoObject = [data];

    		// Create geojson object, add to map and add line to it
    		var trip = L.geoJson();
    		trip.addTo(_map);
    		trip.addData(geoObject[0]);

    		// Set styling
    		trip.setStyle(lineStyle);

    		// Fit bounds to line
    		_map.fitBounds(trip.getBounds());

    		if(style.endIcon) {
    			var marker = L.marker([geoObject[0].coordinates[geoObject[0].coordinates.length-1][1], geoObject[0].coordinates[geoObject[0].coordinates.length-1][0]], {icon: endIcon});
                marker.addTo(map).bindPopup('Slutt');
    		}

    		if(style.startIcon) {
    			var marker = L.marker([geoObject[0].coordinates[0][1], geoObject[0].coordinates[0][0]], {icon: startIcon});
                marker.addTo(map).bindPopup('Start');
    		}
    	});

    };

    var getLineFromServer = function() { //private
    	// get line from server
    }; 
    var uploadStyle = function() { //private

    	// Upload JSON to save changes to style
	        $.ajax({
	          type: "POST",
	          url: "http://localhost:5000/"+id+"/setStyle",
	          data: JSON.stringify(style),
	          success: function (response) {
	                
	            },
	            error: function (response) {
	              
	            },
	          contentType: "application/json",
	          dataType: "json"
	        });
    }; 
    var downloadStyle = function() { //private

    	// Download style and set all style variables
    	$.getJSON('/'+id+'/metadata', function (data) { 
    		style = data.style
    	});

    }; 

};
