// Check if browser supports fileinput
$(function(){
    var message = '<p>Du bruker dessverre en gammel nettleser som ikke støtter mange av dagens funksjoner på internett.</p>'
    message += '<p>Det fører til at du ikke kan laste opp GPS-spor på deltur.no<p> '
    message += '<p>deltur.no anbefaler deg å oppgradere din nettleser før du deler turen din. <p> '

    var elem = document.createElement('input');
    elem.type = 'file';
    if(elem.disabled) {

        BootstrapDialog.show({
            title: 'Beklager!',
            cssClass: 'ie9-dialog',
            message: message,
            buttons: [{
                label: 'OK',
                action: function(dialogref){
                    dialogref.close();
                }
            }]
        }); 


    } 
});