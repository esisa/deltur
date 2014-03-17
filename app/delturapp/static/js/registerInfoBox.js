// Shows a info box when a user registers for the first time. 

$(function () { 
    // Only show if local storage is present and infobox is not shown earlier
    if (Modernizr.localstorage && localStorage["registerInfoBoxShown"] != "yes") {
        var tour = new Shepherd.Tour({
          defaults: {
            classes: 'shepherd-theme-arrows',
            scrollTo: true
          }
        });

        tour.addStep('example-step', {

          text: '<strong>Takk for at du registrerte deg på deltur.no!</strong> <br><br>Ved å klikke på e-posten ovenfor så kan<br> du administrere dine turer.',
          tetherOptions: {
            offset: '-10 0'
          },
          attachTo: '#logout-link bottom',
          classes: 'shepherd-theme-arrows',
          buttons: [
            {
              text: 'Ok',
              action: tour.next
            }
          ]
        });

        tour.start();

        // Show it only once to the user
        localStorage["registerInfoBoxShown"] = "yes";
    }
});