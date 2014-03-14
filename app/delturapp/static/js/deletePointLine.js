
function openDeletePointDialog() {
    var point = points[$('#current-point').val()];

    BootstrapDialog.show({
        title: 'Slette markør',
        cssClass: 'delete-dialog',
        message: 'Ønsker du virkelig å slette denne markøren!',
        buttons: [{
            label: 'Avbryt',
            action: function(dialogref){
                dialogref.close();
            }
        }, {
            label: 'Slett',
            cssClass: 'btn-danger',
            action: function(dialogref){
                dialogref.close();
                deletePoint(point, $('#current-point').val());
            }
        }]
    });  
}

function deletePoint(point, arrayNum) {

    $.ajax({
        url: '/' + point.getId(),
        type: 'DELETE',
        dataType: "json"
    }).done(function(json) {
        point.removeFromMap(map);
        points.splice(arrayNum, 1);
        showMainSidebar();
        humane.log("<p>Markøren er slettet</p>", { timeout: 2000});
    }).fail(function(json) {
        humane.log("<p>Klarte dessverre ikke å slette markøren!</p>", { timeout: 2000});
    });;

}



function openDeleteLineDialog() {
    var line = lines[$('#current-line').val()];

    BootstrapDialog.show({
        title: 'Slette sporet',
        cssClass: 'delete-dialog',
        message: 'Ønsker du virkelig å slette denne sportet!',
        buttons: [{
            label: 'Avbryt',
            action: function(dialogref){
                dialogref.close();
            }
        }, {
            label: 'Slett',
            cssClass: 'btn-danger',
            action: function(dialogref){
                dialogref.close();
                deleteLine(line, $('#current-line').val())
            }
        }]
    });  
}

function deleteLine(line, arrayNum) {

    $.ajax({
        url: '/' + line.getId(),
        type: 'DELETE',
        dataType: "json"
    }).done(function(json) {
        line.removeFromMap(map);
        lines.splice(arrayNum, 1);
        showMainSidebar()
        humane.log("<p>Sporet er slettet</p>", { timeout: 2000});
    }).fail(function(json) {
        humane.log("<p>Klarte dessverre ikke å slette sporet!</p>", { timeout: 2000});
    });;

}
