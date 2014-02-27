var delturPoint = function () {


    var id;
    var status = 0;
    var point = L.geoJson();
    var lat, lon;
    var custom_popup_footer = "";
    var imgMarker;

    var style =  {
                    "popup": {
                        "show": true,
                        "description": "",
                        "title": "",
                        "image": {
                            "url": "",
                            "width": -1//,
                            /*"height": -1*/
                        },
                    },
                    "label": {
                        "text": "",
                        "static": false
                    },
                    "markersymbol": "map-marker",
                    "markerType": "fa",
                    "markercolor": "blue"
                };

    var picture = L.AwesomeMarkers.icon({
      prefix: 'fa',
      icon: 'picture-o', 
      markerColor: 'blue'
    });
    var emptyIcon = L.AwesomeMarkers.icon({
      prefix: 'fa',
      icon: 'map-marker', 
      markerColor: 'blue'
    });

    this.initWithId = function (_id) {
    	setId(_id);
    	downloadStyle();
    };

    this.init = function (_lat, _lon, _title, _description, _imgUrl) {  //public
        style.popup.image.url = _imgUrl;
        style.popup.title = _title;
        style.popup.description = _description;

        var url = delPointURL + _lat +"/"+ _lon + delPointToken;
        var jsonData =  JSON.stringify({"title": style.popup.title,"description":style.popup.description,"url": style.popup.image.url});          
        lat = _lat;
        lon = _lon;

        $.ajax({
            type: "POST",
            url: url,
            data: jsonData,
            contentType : 'application/json',
            success: function (response) {
                id = response.id;
                status = 1;
            },
            error: function (response) {
                status = -1; // Error in uploaded file
            }
        });

    };

    this.updateStyle = function () { //public
        downloadStyle();
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

    this.getUrl = function () {  //public
        return style.popup.image.url;
    };

    this.getLat = function () {  //public
        return lat;
    };

    this.getLon = function () {  //public
        return lon;
    };

    this.getTitle = function () {  //public
        return style.popup.title;
    };
    this.setTitle = function (_title) {  //public
        style.popup.title = _title;
    };

    this.getImgUrl = function () {  //public
        return style.image.url;
    };
    this.setImgUrl = function (_imgUrl) {  //public
        style.image.url = _imgUrl;
    };

    this.getDescription = function () {  //public
         return style.popup.description;
    };
    this.setDescription = function (_description) {  //public
        style.popup.description = _description;
    };

    this.getMarkerSymbol = function () {  //public
        return style.markersymbol;
    };

    this.getMarkerType = function () {  //public
        return style.markerType;
    };

    this.setStyle = function (_style) {  //public

    	// Check if _style is valid??
        style = _style;
        uploadStyle();
    };

    this.saveStyle = function () {  //public
        uploadStyle();
    };

    this.getStyle = function () {  //public
        return style;
    };

    this.getGeom = function () {  //public
        $.getJSON('/'+id+'/geojson', function (data) {
    		geoObject = [data];
    		
    	});
    	return "geoObject";
    };

    this.removeFromMap = function (_map) {
        _map.removeLayer(imgMarker);
    };

    this.updateRendering = function (_map) {  //public
    	//_map.removeLayer(point);

    	addToMap(_map);
    }

    this.renderToMap = function (_map) {  //public
    	addToMap(_map);
    }

    this.getPoint = function () { // public
        return L.latLng(lat, lon);
    }

    this.getBounds = function() { //public
        var p1 = L.point(lon, lat);
        var p2 = L.point(lon, lat);
        return L.bounds(p1, p2);
    }

    this.addCustomPopupFooter = function (_custom_popup_footer) {  //public
        custom_popup_footer = _custom_popup_footer;
    }

    var addToMap = function (_map) {  // private

        
        if(style.markerType == "number") {
            var icon = L.AwesomeMarkers.icon({
                text: style.markersymbol,
                color: style.markercolor
            });
    
        }
        else { // font awesome
            var icon = L.AwesomeMarkers.icon({
              prefix: 'fa',
              icon: style.markersymbol, 
              markerColor: style.markercolor//,
              //iconColor: 'black'
            });
        }


        imgMarker = L.marker([lat, lon], {icon: icon});

        if(style.popup.image.width==-1 && style.popup.image.width==-1) {
            var imgWidth = $('body').width()*0.4; // Use body width to calculate image width
        
            // Make sure the image is never larger than 250 px
            if(imgWidth>250)
                imgWidth = 250;
        }
        else {
            imgWidth = style.popup.image.width;
        }
        
        // Add label
        if(style.label.text != "") {
            imgMarker.bindLabel(style.label.text, {noHide: style.label.static});
        }

        // Add marker to map
        imgMarker.addTo(map);

        $([style.popup.image.url]).preload(); // Preload image

        _map.closePopup(); // Close poup to make sure title/description/image er rerendered

        if(typeof style.popup.image.url == "undefined") {
            imageHtml = '';
        }
        else {
            if(style.popup.image.url != "")
                imageHtml ='<img width="'+imgWidth+'" src="'+ style.popup.image.url +'"><br>';
            else
                imageHtml = '';
        }

        if(style.popup.show) // Show popup
            imgMarker.bindPopup('<h3 id="popupText_title" style="width:'+imgWidth+'px">'+style.popup.title+'</h3>'+imageHtml+'<div id="popupText_description" style="width:'+imgWidth+'px">' + style.popup.description + '</div>' + custom_popup_footer, {"minWidth": imgWidth + 20});
        else if(custom_popup_footer != "") // Only show popup in edit mode
            imgMarker.bindPopup('<p>Popup vil ikke vises i ferdig tur.</p>' + custom_popup_footer);

        


    };

    var getPointFromServer = function() { //private
    	// get line from server
    }; 
    var uploadStyle = function() { //private

    	// Upload JSON to save changes to style
        $.ajax({
          type: "POST",
          url: "/"+id+setStyleUrl,
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
        status = 0;

    	// Download style and set all style variables
    	$.getJSON('/'+id+'/metadata', function (data) { 
    		style = data.style
            lat = data.lat
            lon = data.lon
            title = data.style.popup.title
            description = data.style.popup.description
    		status = 1;
    	});

    }; 

};
