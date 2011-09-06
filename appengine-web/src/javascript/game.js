$(document).ready(function() {
    var gameUrl = '/api/',
        MAX_LINES = 50,
        templates,
        channel,
        handledActions = [];

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
            //if (console && console.log) console.log('Read templates:', templates);
        }
        return templates;
    }

    function onAction(data, textStatus, jqXhr) {
        //if (console && console.log) console.log('Success!', data, textStatus, jqXhr);
        handleAction(data);
    }

    function onError(jqXHR, textStatus, errorThrown) {
        if (console && console.log) console.log('Error!', jqXHR, textStatus, errorThrown);
    }

    function onStats(data, textStatus, jqXhr) {
        var hero;
        if (!data['data'] || !data['data']['hero']) return;
        hero = data['data']['hero']
        //if (console && console.log) console.log('Got stats!', data, textStatus, jqXhr);
        updateCharsheet(hero);
    }

    function ajaxAction(cmd, successFn, url, data) {
        data = data || {};
        if (!data['format']) data['format'] = 'json';
        url = url || gameUrl;
        $.ajax({
            url: url + cmd,
            data: data,
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

    function clearLines() {
        var id, el;
        while (handledActions.length > MAX_LINES) {
            id = handledActions.shift();
            el = $('#action_' + id);
            //if (console && console.log) console.log('Removing action:', id, el);
            el.remove();
        }
    }

    function ucfirst(string)
    {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    function getActionClass(cmd) {
        return 'action' + ucfirst(cmd);
    }

    function handleAction(data) {
        var line, cls;
        if ($.inArray(data.id, handledActions) >= 0) {
            //if (console && console.log) console.log('Action already handled:', data.id);
            // Highlight line.
            $('#action_' + data.id).effect("highlight", {}, 500);
            return;
        }

        // Make sure this action isn't handled again.
        handledActions.push(data.id);

        // Update character sheet with new data.
        if (data['data'] && data['data']['hero']) {
            updateCharsheet(data['data']['hero']);
        }

        // Add action to list.
        cls = getActionClass(data['command']);
        line = $.tache(getTemplates().actionline, { 'line': data.message, 'id': data.id, cls: cls });
        $('#actionList').append(line);


        // Remove old lines.
        clearLines();
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
                //if (console && console.log) console.log('field', field, 'value', hero[field]);
                var valueDiv = $('#' + field + 'Value');
                if (valueDiv) {
                    valueDiv.html(hero[field]);
                }
            }
        }
    }

    function onCreateChannel(data, textStatus, jqXhr) {
        var token;
        if (console && console.log) console.log('Channel created:', data, textStatus, jqXhr);
        try {
            channel_token = data['channel_token'];
            channel_client_id = data['channel_client_id'];
            channel = setup_channel(channel_token);
        } catch (e) {
            if (console && console.log) console.log('Failed setting up channel.', e);
        }
    }

    function onChannelOpened() {
        //if (console && console.log) console.log('Channel was opened');
    }

    function onChannelMessage(message) {
        var data;
        //if (console && console.log) console.log('Received message from channel:', message);
        if (message.data) {
            data = $.parseJSON(message.data);
            handleAction(data);
        }
    }

    function onChannelError(error) {
        if (console && console.log) console.log('Received an error from the channel:', error);
    }

    function onChannelClose() {
        if (console && console.log) console.log('Channel was closed.');
        // TODO: Request a new client_id and channel.
        ajaxAction('createchannel', onCreateChannel, '/', { client_id: channel_client_id });
    }

    function setup_channel(token) {
        var channel = new goog.appengine.Channel(token);
        socket = channel.open({
            onopen: onChannelOpened,
            onmessage: onChannelMessage,
            onerror: onChannelError,
            onclose: onChannelClose
        });
        return channel;
    }

    function setup() {
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

        // Setup channel
        channel = setup_channel(channel_token);
    }

    // Call setup function.
    setup();

});

