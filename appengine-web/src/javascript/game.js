$(document).ready(function() {
    var gameUrl = '/api/';
    var templates;

    function getTemplate(name) {
        var template = $('#' + name + 'Template').html();
        return template;
    }

    function getTemplates() {
        if (!templates) {
            templates = {
                'actionline': getTemplate('actionline'),
                'charsheet': getTemplate('charsheet')
            };
            if (console && console.log) console.log('Read templates:', templates);
        }
        return templates;
    }

    function ajaxAction(cmd, successFn) {
        $.ajax({
            url: gameUrl + cmd,
            headers: { 
                //'Accept': 'text/plain; charset=utf-8',
                'Accept': 'application/json',
                'Content-Type': 'text/plain; charset=utf-8'
            },
            dataType: 'json',
            success: successFn || onAction,
            error: onError
        });
    }

    function onAction(data, textStatus, jqXhr) {
        var line;
        if (console && console.log) console.log('Success!', data, textStatus, jqXhr);
        //var line = $("<span class='actionLine'>" + data + "</span>");
        //$('#actionsDiv').append(line);
        //var line = $("<li class='actionLine'>" + data + "</li>");
        line = $.tache(getTemplates().actionline, { 'line': data.message });
        if (data['data'] && data['data']['hero']) {
            updateCharsheet(data['data']['hero']);
        }
        $('#actionList').append(line);
    }

    function onError(jqXHR, textStatus, errorThrown) {
        if (console && console.log) console.log('Error!', jqXHR, textStatus, errorThrown);
    }

    function onStats(data, textStatus, jqXhr) {
        var hero;
        if (!data['data'] || !data['data']['hero']) return;
        hero = data['data']['hero']
        if (console && console.log) console.log('Got stats!', data, textStatus, jqXhr);
        //var re = /^Stats: /;
        //data = data.message.replace(re, '');
        //$('#heroDiv').html(data);
        updateCharsheet(hero);
    }

    function updateCharsheet(hero) {
        var heroDiv = $('#heroDiv');
        if (hero.hasOwnProperty('health') && hero.hasOwnProperty('hurt')) {
            hero['current_health'] = (hero['health'] - hero['hurt']);
            hero['hurthealth'] = '' + hero['current_health'] + '/' + hero['health'];
        }
        //if (console && console.log) console.log('heroDiv:' + heroDiv.html() + '|', 'hero', hero);
        if ($.trim(heroDiv.html()) == '') {
            var stats = $.tache(getTemplates().charsheet, hero);
            heroDiv.html(stats);
        } else {
            for (var field in hero) if (hero.hasOwnProperty(field)) {
                if (console && console.log) console.log('field', field, 'value', hero[field]);
                var valueDiv = $('#' + field + 'Value');
                if (valueDiv) {
                    valueDiv.html(hero[field]);
                }
            }
        }
    }

    // Setup command buttons
    $('.commandBtn').live('click', function(event) {
        var cmd = $(this).attr('name'),
            fn = (cmd == 'stats') ? onStats : onAction;
        ajaxAction(cmd, fn);
    });

    // Update charsheet when clicked.
    $('#heroDiv').live('click', function(event) {
        ajaxAction('stats', onStats);
    });

    // Add highlight when hovering over task buttons.
    $('.taskImg').hover(
        function(ev) {
            var el = $(this);
            var img = el.attr('src');
            el.attr('src', 'images/icon-hover.png');
            el.css('background', 'url(' + img + ')');
        },
        function(ev) {
            var el = $(this);
            var img = 'images/icon-' + el.attr('alt').toLowerCase() + '.png';
            el.attr('src', img);
            el.css('background', '');
        }
    );

    // Load stats.
    ajaxAction('stats', onStats);

});
