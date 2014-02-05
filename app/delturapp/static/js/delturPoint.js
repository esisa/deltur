var delturPoint = function () {


    var id;
    var title = "";
    var description = "";
    var status = 0;
    var point = L.geoJson();
    var lat, lon;
    var custom_popup_footer = "";

    var style = {
                    "image": {
                        "url": "",
                        "width": -1,
                        "height": -1
                    },
                    "label": {
                        "text": "",
                        "static": false
                    },
                    "markersymbol": "map-marker",
                    "markerType": "fa",
                    "markercolor": "blue",
                    "markerpopup": true
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
        style.image.url = _imgUrl;
        title = _title;
        description = _description;

        var url = "/del/sted/" + _lat +"/"+ _lon;
        var jsonData =  JSON.stringify({"title": title,"description":description,"url": style.image.url});          
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

    var setId = function(_id) { //private
    	id = _id;
    };

    this.getId = function () {  //public
        return id;
    };

    this.getStatus = function () {  //public
        return status;
    };

    this.getLat = function () {  //public
        return lat;
    };

    this.getLon = function () {  //public
        return lon;
    };

    this.getTitle = function () {  //public
        return title;
    };
    this.setTitle = function (_title) {  //public
        title = _title;
    };

    this.getImgUrl = function () {  //public
        return style.image.url;
    };
    this.setImgUrl = function (_imgUrl) {  //public
        style.image.url = _imgUrl;
    };

    this.getDescription = function () {  //public
         return description;
    };
    this.setDescription = function (_description) {  //public
        description = _description;
    };

    this.getMarkerSymbol = function () {  //public
        return style.markersymbol;
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


        var imgMarker = L.marker([lat, lon], {icon: icon});
        var imgWidth = $('body').width()*0.4; // Use body width to calculate image width
        
        // Make sure the image is never larger than 250 px
        if(imgWidth>250)
            imgWidth = 250;

        // Add label
        if(style.label.text != "") {
            imgMarker.bindLabel(style.label.text, {noHide: style.label.static});
        }

        imgMarker.addTo(map).bindPopup('<h3 id="popupText_title" style="width:'+imgWidth+'px">'+title+'</h3><img width="'+imgWidth+'" src="'+ style.image.url +'"><br><div id="popupText_description" style="width:'+imgWidth+'px">' + description + '</div>' + custom_popup_footer);
        $([style.image.url]).preload(); // Preload image

    

    };

    var getPointFromServer = function() { //private
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
            lat = data.lat
            lon = data.lon
            title = data.title
            description = data.description
    		status = 1;
    	});

    }; 

};
