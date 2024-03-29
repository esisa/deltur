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
    var custom_popup_footer = "";
    var geoObject;
    var editable = false;

    this.initWithId = function (_id) {
    	setId(_id);
        $.getJSON('/'+id+'/geojson', function (data) {
            geoObject = [data];
     
            downloadStyle();
        });
    	
    };

    this.initWithGeo = function (_geo, _title, _description) {
        style.popup.title = _title;
        style.popup.description = _description;
        geoObject =  _geo ;

        //Upload to deltur.no/del/gpx
        $.ajax({
          type: "POST",
          url: delGeoJSONURL,
          data: JSON.stringify(geoObject[0]),
          success: function (response) {
                id = response.id;

                uploadStyle();
                //downloadStyle();
            },
            error: function (response) {
              status = -1; // Error in uploaded file
            },
          contentType: "application/json",
          dataType: "json"
        });


        
 
        
        
    };

    this.init = function (_url, _title, _description) {  //public
        style.popup.title = _title;
        style.popup.description = _description;

        var fpfile = {url: _url, filename: 'hello.txt', mimetype: 'text/plain', isWriteable: false, size: 100};
        filepicker.read(fpfile, function(data){

	        //Upload to deltur.no/del/gpx
	        $.ajax({
	          type: "POST",
	          url: delGPXURL,
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

    this.updateStyle = function () { //public
        downloadStyle();
    }

    

    var getPopup = function() { //private
        return '<h3 id="popupText_title">'+style.popup.title+'</h3><div id="popupText_description">' + style.popup.description + '</div>' + custom_popup_footer;
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

    this.getColor = function () {  //public
         return style.color;
    };
    this.setColor = function (_color) {  //public
        style.color = _color;
    };

    this.getWidth = function () {  //public
         return style.width;
    };
    this.setWidth = function (_width) {  //public
        style.width = _width;
    };

    this.getOpacity = function () {  //public
         return style.opacity;
    };
    this.setOpacity = function (_opacity) {  //public
        style.opacity = _opacity;
    };

    this.getLabelText = function () {  //public
         return style.label.text;
    };
    this.setLabelText = function (_text) {  //public
        style.label.text = _text;
    };

    this.getPopup = function () {  //public
         return style.popup.show;
    };
    this.setPopup = function (_show) {  //public
        style.popup.show = _show;
    };

    this.getStartIcon = function () {  //public
         return style.start_icon;
    };
    this.setStartIcon = function (_show) {  //public
        style.start_icon = _show;
    };

    this.getEndIcon = function () {  //public
         return style.end_icon;
    };
    this.setEndIcon = function (_show) {  //public
        style.end_icon = _show;
    };

    this.getStyle = function () {  //public
        return style;
    };

    this.setStyle = function (_style) {  //public

    	// Check if _style is valid??
        style = _style;
        uploadStyle();
    };

    this.saveStyle = function () {  //public
        uploadStyle();
    };

    this.getGeom = function () {  //public
        /*$.getJSON('/'+id+'/geojson', function (data) {
    		geoObject = [data];
    		
    	});*/
    	return geoObject[0];
    };

    this.removeFromMap = function (_map) {
        _map.removeLayer(trip);
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

    this.addCustomPopupFooter = function (_custom_popup_footer) {  //public
        custom_popup_footer = _custom_popup_footer;
    }

    var editFunction, currentPlaceInArray;
    this.makeEditable = function (_editFunction, _currentPlaceInArray) {  //public
        editable = true;
        editFunction = _editFunction;
        currentPlaceInArray = _currentPlaceInArray;
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

                if(editable) {
                    layer.on("click", function (e) {
                        editFunction(id, currentPlaceInArray);
                    });
                }

                if(style.popup.show)
                    layer.bindPopup(getPopup());
                //else if(custom_popup_footer != "") // Only show popup in edit mode
                //    layer.bindPopup('<p>Popup vil ikke vises i ferdig tur.</p>' + custom_popup_footer);
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
          url: "/"+id+setStyleUrl,
          // "/" + id+"/" + setStyleUrl
          data: JSON.stringify(style),
          success: function (response) {
                status = 1;
            },
            error: function (response) {
              
            },
          contentType: "application/json",
          dataType: "json"
        });
    }; 
    var downloadStyle = function() { //private
        status = 0;

    	// Download style and set all style variables
    	$.getJSON('/'+id+'/metadata', function (data) { 
    		style = data.style
    		status = 1;
    	});

    }; 

};
