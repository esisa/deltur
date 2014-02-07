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

    var style = {
                    "opacity": 0.65,
                    "popup": {
                        "title": "",
                        "description": "",
                        "show": false
                    },
                    "label": {
                        "text": ""
                    },
                    "end_icon": false,
                    "color": "#ff7800",
                    "width": 5.0,
                    "start_icon": false
                };

    var id;
    var status = 0;
    var trip = L.geoJson();
    var geo;
    var startMarker, endMarker;

    this.initWithId = function (_id) {
    	setId(_id);
        $.getJSON('/'+id+'/geojson', function (data) {
            geoObject = [data];
     
            downloadStyle();
        });
    	
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

                    $.getJSON('/'+id+'/geojson', function (data) {
                        geoObject = [data];
                        status = 1;
                    });
                    
	            },
	            error: function (response) {
	              status = -1; // Error in uploaded file
	            },
	          contentType: "application/gpx+xml",
	          dataType: "json"
	        });
            
        }); // END FILEPICKER
    };

    var getPopup = function() { //private
        return '<h3 id="popupText_title">'+style.popup.title+'</h3><div id="popupText_description">' + style.popup.description + '</div>'
    }

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
        return style.popup.title;
    };
    this.setTitle = function (_title) {  //public
        style.popup.title = _title;
    };

    this.getDescription = function () {  //public
         return style.popup.description;
    };
    this.setDescription = function (_description) {  //public
        style.popup.description = _description;
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
    	return geoObject[0];
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

    this.getBounds = function() { //public
        return trip.getBounds();
    }

    var addToMap = function (_map) {  // private

    	var lineStyle = {
            "color": style.color,
            "weight": style.width,
            "opacity": style.opacity
        };

		// Create geojson object, add to map and add line to it
        trip = L.geoJson(geoObject[0], {
            onEachFeature: function (feature, layer) {
                if(style.popup.show)
                    layer.bindPopup(getPopup());
            }
        });
		trip.addTo(_map);
		
        // Add label
        if(style.label.text != "") {
            trip.bindLabel(style.label.text);
        }

        
		// Set styling
		trip.setStyle(lineStyle);



		if(style.end_icon) {
			startMarker = L.marker([geoObject[0].coordinates[geoObject[0].coordinates.length-1][1], geoObject[0].coordinates[geoObject[0].coordinates.length-1][0]], {icon: endIcon});
            startMarker.addTo(map).bindPopup('Slutt');
		}

		if(style.start_icon) {
			endMarker = L.marker([geoObject[0].coordinates[0][1], geoObject[0].coordinates[0][0]], {icon: startIcon});
            endMarker.addTo(map).bindPopup('Start');
		}
    	

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
