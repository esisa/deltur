L.Control.MarkerList = L.Control.extend({
    options: {
        position: 'topright',
    },

    onAdd: function (map) {
        var controlDiv = L.DomUtil.create('div', 'leaflet-control-command');
        L.DomEvent
            .addListener(controlDiv, 'click', L.DomEvent.stopPropagation)
            .addListener(controlDiv, 'click', L.DomEvent.preventDefault)
        .addListener(controlDiv, 'click', function () { sidebar.show(); });

        var controlUI = L.DomUtil.create('div', 'leaflet-control-marker-list', controlDiv);
        controlUI.title = 'Punkter i kartet';
        return controlDiv;
    }
});