function setPointMarkerSymbol(point, value) {
    point.setMarkerSymbol(value);
    point.saveStyle();
    point.updateRendering(map);
}
    


$(function(){

    $( "#point-title" ).blur(function() {
        var point = points[$('#current-point').val()];
        point.setTitle($('#point-title').val());
        point.saveStyle();
        point.updateRendering(map);
    });

    $( "#point-description" ).blur(function() {
        var point = points[$('#current-point').val()];
        point.setDescription($('#point-description').val());
        point.saveStyle();
        point.updateRendering(map);
    });

    // Image
    // Image size

    $('#point-check-popup').change(function() {
        var point = points[$('#current-point').val()];
        if($(this).is(":checked")) {
            point.setPopup(true);
        } else {
            point.setPopup(false);
        }
        point.saveStyle();
        point.updateRendering(map);
    });

    $("#point-color" ).blur(function() {
        var point = lines[$('#current-point').val()];
        point.setColor($('#point-color').val());
        point.saveStyle();
        point.updateRendering(map);
    });


    $('#point-marker-type').change(function() {
        var markerType = $(this).find('option:selected').val(); 
        var point = points[$('#current-point').val()];
        if(markerType=="Fontawesome") {
            point.setMarkerType("fa");

            // Change to different input
            $("#point-marker-text-div").show();
            $("#point-marker-number-div").hide();

            // Update marker after changing input
            var value = $('#point-marker-text').val();
            setPointMarkerSymbol(point, value);
        }
        else {
            point.setMarkerType("number");

            // Change to different input
            $("#point-marker-text-div").hide();
            $("#point-marker-number-div").show();

            // Update marker after changing input
            var value = $('#point-marker-number').val();
            setPointMarkerSymbol(point, value);
        }
        point.saveStyle();
        point.updateRendering(map);
    });

    
    $( "#point-marker-text" ).keyup(function() {
        var point = points[$('#current-point').val()];
        var value = $('#point-marker-text').val();
        setPointMarkerSymbol(point, value) 
    });

    $( "#point-marker-number" ).keyup(function() {
        var point = points[$('#current-point').val()];
        var value = $('#point-marker-number').val();
        setPointMarkerSymbol(point, value) 
    });


    $( "#point-label-text" ).keyup(function() {
        var point = points[$('#current-point').val()];
        point.setLabelText($('#point-label-text').val());
        point.saveStyle();
        point.updateRendering(map);
    });

    

    $('#point-label-static').change(function() {
        var point = points[$('#current-point').val()];
        if($(this).is(":checked")) {
            point.setLabelStatic(true);
        } else {
            point.setLabelStatic(false);
        }
        point.saveStyle();
        point.updateRendering(map);
    });




    $('#point-image-button').click(function() {
        // Image upload
        filepicker.pickAndStore(
        {
            mimetype:"image/*",
            services:['COMPUTER', 'FACEBOOK', 'DROPBOX', 'GOOGLE_DRIVE',  'FLICKR', 'PICASA', 'INSTAGRAM', 'URL'],
            multiple: false,
            maxFiles: 1,
            maxSize: 3145728
        },
        {location:"S3", access: 'public'}, 
        function(fpfiles){
            //console.log(JSON.stringify(fpfiles));
            
            $.each(fpfiles, function(index, file) {
                var point = points[$('#current-point').val()];
                point.setImgUrl(file.url);
                point.saveStyle();
                point.updateRendering(map);

                $('#point-image-button').html("Endre bilde");
            });
            
        },
        function(FPError){
            console.log(FPError.toString());
        });
    });
    

});


