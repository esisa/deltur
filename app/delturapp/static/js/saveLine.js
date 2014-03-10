

$(function(){

    $( "#line-title" ).blur(function() {
        var line = lines[$('#current-line').val()];
        line.setTitle($('#line-title').val());
        line.saveStyle();
        line.updateRendering(map);
    });

    $( "#line-description" ).blur(function() {
        var line = lines[$('#current-line').val()];
        line.setDescription($('#line-description').val());
        line.saveStyle();
        line.updateRendering(map);
    });


    $( "#line-width" ).keyup(function() {
        var line = lines[$('#current-line').val()];
        line.setWidth($('#line-width').val());
        line.saveStyle();
        line.updateRendering(map);
    });

    $( "#line-color" ).blur(function() {
        var line = lines[$('#current-line').val()];
        line.setColor($('#line-color').val());
        line.saveStyle();
        line.updateRendering(map);
    });

    $( "#line-opacity" ).blur(function() {
        var line = lines[$('#current-line').val()];
        line.setOpacity($('#line-opacity').val());
        line.saveStyle();
        line.updateRendering(map);
    });

    $( "#line-label-text" ).keyup(function() {
        var line = lines[$('#current-line').val()];
        line.setLabelText($('#line-label-text').val());
        line.saveStyle();
        line.updateRendering(map);
    });

    $('#line-check-popup').change(function() {
        var line = lines[$('#current-line').val()];
        if($(this).is(":checked")) {
            line.setPopup(true);
        } else {
            line.setPopup(false);
        }
        line.saveStyle();
        line.updateRendering(map);
    });

    $('#line-check-start').change(function() {
        var line = lines[$('#current-line').val()];
        if($(this).is(":checked")) {
            line.setStartIcon(true);
        } else {
            line.setStartIcon(false);
        }
        line.saveStyle();
        line.updateRendering(map);
    });

    $('#line-check-end').change(function() {
        var line = lines[$('#current-line').val()];
        if($(this).is(":checked")) {
            line.setEndIcon(true);
        } else {
            line.setEndIcon(false);
        }
        line.saveStyle();
        line.updateRendering(map);
    });

    $('#line-opacity').change(function() {
        var opacity = $(this).find('option:selected').val(); 
        var line = lines[$('#current-line').val()];
        line.setOpacity(opacity);
        line.saveStyle();
        line.updateRendering(map);
    });

});


