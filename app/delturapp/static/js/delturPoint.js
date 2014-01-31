var delturPoint = function () {


    var id;
    var title = "";
    var description = "";
    var imgUrl = "";
    var status = 0;
    var point = L.geoJson();
    var style;
    var lat, lon;

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

    this.init = function (_lat, _lon) {  //public

        var url = "/del/sted/" + _lat +"/"+ _lon;
        var jsonData =  JSON.stringify({"title": title,"description":description,"url": imgUrl});          
        lat = _lat;
        lon = _lon;

        $.ajax({
            type: "POST",
            url: url,
            data: jsonData,
            contentType : 'application/json',
            success: function (response) {
                id = response.id;
                status = 1; // File is uploaded

                // Update style from server
                downloadStyle();
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
        return imgUrl;
    };
    this.setImgUrl = function (_imgUrl) {  //public
        imgUrl = _imgUrl;
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

    this.saveStyle = function () {  //public
        uploadStyle();
    };

    this.getGeom = function () {  //public
        $.getJSON('/'+id+'/geojson', function (data) {
    		geoObject = [data];
    		
    	});
    	return "geoObject";
    };

    this.updateRendering = function (_map) {  //public
    	_map.removeLayer(point);

    	addToMap(_map);
    }

    this.renderToMap = function (_map) {  //public
    	addToMap(_map);
    }

    var addToMap = function (_map) {  // private

        var imgMarker;

        if(style.image.url != "")
            imgMarker = L.marker([lat, lon], {icon: picture});
        else
            imgMarker = L.marker([lat, lon], {icon: emptyIcon});
        var imgWidth = $('body').width()*0.4; // Use body width to calculate image width
        
        // Make sure the image is never larger than 250 px
        if(imgWidth>250)
            imgWidth = 250;
        
        imgMarker.addTo(map).bindPopup('<h3 id="popupText_title" style="width:'+imgWidth+'px">'+title+'</h3><img width="'+imgWidth+'" src="'+ style.image.url +'"><br><div id="popupText_description" style="width:'+imgWidth+'px">' + description + '</div>');
        $([style.image.url]).preload(); // Preload image

    

    };

    var getPointFromServer = function() { //private
    	// get line from server
    }; 
    var uploadStyle = function() { //private

        debugger;

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
    		status = 1;
    	});

    }; 

};
