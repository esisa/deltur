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
    var trip = L.geoJson();
    var style;
    var startMarker, endMarker;

    this.initWithId = function (_id) {
    	setId(_id);
    	downloadStyle();
    };

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

	                // Update style from server
	                downloadStyle();

                    // Status is set in downloadStyle
	            },
	            error: function (response) {
	              status = -1; // Error in uploaded file
	            },
	          contentType: "application/gpx+xml",
	          dataType: "json"
	        });
            
        }); // END FILEPICKER
    };

    var setId = function(_id) { //private
    	id = _id;
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

    this.getGeom = function () {  //public
        $.getJSON('/'+id+'/geojson', function (data) {
    		geoObject = [data];
    		
    	});
    	return "geoObject";
    };

    this.updateRendering = function (_map) {  //public
    	_map.removeLayer(trip);
    	try { _map.removeLayer(startMarker); } catch(err) {}
    	try { _map.removeLayer(endMarker); } catch(err) {}
    	addToMap(_map);
    }

    this.addHover = function (_markerGroup) {  //public
    	trip.on('mouseover', function(e) {
            _markerGroup.clearLayers(); 
            var marker = new L.CircleMarker(e.latlng);
            _markerGroup.addLayer(marker);
        });
    }

    this.renderToMap = function (_map) {  //public
    	addToMap(_map);
    }

    var addToMap = function (_map) {  // private

    	var lineStyle = {
            "color": style.color,
            "weight": style.width,
            "opacity": style.opacity
        };

        // Get GeoJSON and add to map
    	$.getJSON('/'+id+'/geojson', function (data) {
    		geoObject = [data];

    		// Create geojson object, add to map and add line to it
    		trip.addTo(_map);
    		trip.addData(geoObject[0]);

    		// Set styling
    		trip.setStyle(lineStyle);

    		// Fit bounds to line
    		_map.fitBounds(trip.getBounds());

    		if(style.end_icon) {
    			startMarker = L.marker([geoObject[0].coordinates[geoObject[0].coordinates.length-1][1], geoObject[0].coordinates[geoObject[0].coordinates.length-1][0]], {icon: endIcon});
                startMarker.addTo(map).bindPopup('Slutt');
    		}

    		if(style.start_icon) {
    			endMarker = L.marker([geoObject[0].coordinates[0][1], geoObject[0].coordinates[0][0]], {icon: startIcon});
                endMarker.addTo(map).bindPopup('Start');
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
          url: "/"+id+"/setStyle",
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
    		status = 1;
    	});

    }; 

};
