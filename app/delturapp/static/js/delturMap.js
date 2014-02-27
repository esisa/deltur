var map = new L.Map('map', {fullscreenControl: true, keyboard: true, attributionControl: true, zoom: 4, center: [65.2 ,10.572]});

map.attributionControl.setPrefix(""); // Fjerner powered by Leaflet
        
/*if($('.container').width()>480) {
    L.control.scale({imperial:false, position: 'bottomleft'}).addTo(map);
}*/

var skikart = L.mapbox.tileLayer(tileJsonSkikart, {
    detectRetina: true,
    // if retina is detected, this layer is used instead
    retinaVersion: tileJsonSkikartHighdef
});

var turkart = L.mapbox.tileLayer(tileJsonTurkart, {
    detectRetina: true,
    // if retina is detected, this layer is used instead
    retinaVersion: tileJsonTurkartHighdef
});

var veikart = L.mapbox.tileLayer('esisa.map-0tz2sd3q');

var topokart = L.mapbox.tileLayer(tileJsonTopokart, {
    detectRetina: true,
    // if retina is detected, this layer is used instead
    retinaVersion: tileJsonTopokartHighdef
});

var satellite = L.mapbox.tileLayer('esisa.map-0s7gv7xn');


var kartverket = new L.TileLayer("http://opencache.statkart.no/gatekeeper/gk/gk.open_gmaps?layers=topo2&zoom={z}&x={x}&y={y}", {
    subdomains: ["1", "2", "3", "4"],
    //scheme: "tms",
    maxZoom: 18
});

// Seems like attribution is not correctly pulled from tilejson so we do it manually
if ( $(window).width() < 800) {
  map.attributionControl.addAttribution('<a data-toggle="modal" href="#termsModal">Kartrettigheter</a>');
}
else
{
  map.attributionControl.addAttribution('<a target="_blank" href="http://skogoglandskap.no">Skog og landskap</a>');
  map.attributionControl.addAttribution('<a target="_blank" href="http://kartverket.no">© Kartverket</a>');
  map.attributionControl.addAttribution('<a target="_blank" href="http://osm.org">© OpenStreetMap-bidragsytere</a>');
} 
