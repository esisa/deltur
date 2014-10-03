
var timeout;
$('.typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1,
  autoselect: true
},
{
 // name: 'states',
  //displayKey: 'stedsnavn',
  templates: {
    empty: [
      '<div class="empty-message">',
      'Ingen tilgjengelige stedsnavn på dette søket',
      '</div>'
    ].join('\n'),
    suggestion: Handlebars.compile('<p><strong>{{stedsnavn}}</strong>, {{kommunenavn}}, {{fylkesnavn}} - {{navnetype}}</p>')
  },
  source: function (query, process) {
        if (timeout) {
            clearTimeout(timeout);
        }
        
        timeout = setTimeout(function() {
            return $.get('/ssrSok', { query: query }, function (data) {
                return process(data.sokRes.stedsnavn);
            });
        }, 300);

        
    }
});

$('#search-field').bind('typeahead:selected', function(obj, datum, name) { 
    console.log("Nord: " + datum.nord + " Øst: "+ datum.aust)     
        map.panTo([datum.nord,datum.aust]);
        map.setZoom(15);

        // Hack to make sure we pan to the correct place
        map.panTo([datum.nord,datum.aust]);
        
        // Move to the right of sidebar
        map.panBy([-$('#sidebar').width()/2, 0]);
});

