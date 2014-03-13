
 
$('.typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
 // name: 'states',
  //displayKey: 'stedsnavn',
  templates: {
    empty: [
      '<div class="empty-message">',
      'Ingen tilgjengelige svar på dette stedsnavnet',
      '</div>'
    ].join('\n'),
    suggestion: Handlebars.compile('<p><strong>{{stedsnavn}}</strong>, {{kommunenavn}}, {{fylkesnavn}} - {{navnetype}}</p>')
  },
  source: function (query, process) {
        return $.get('/ssrSok', { query: query }, function (data) {
            return process(data.sokRes.stedsnavn);
        });
    }
});

$('#search-field').bind('typeahead:selected', function(obj, datum, name) {      
        map.panTo([datum.nord,datum.aust]);
        map.setZoom(15);
        map.panBy([-300, 0]);
});