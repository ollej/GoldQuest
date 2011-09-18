$(document).ready(function() {
    var gameUrl = '/api/',
        MAX_LINES = 50,
        templates,
        metadata = {},
        channel,
        handledActions = [],
        heroStats = {},
        heroDiv;

    // Log if console.log exists and we are running on localhost
    function log() {
        if (console && console.log && document.domain == 'localhost') {
            console.log.apply(console, arguments)
        }
    }

    function getTemplate(name) {
        var template = $('#' + name + 'Template').html();
        return template;
    }

    function getTemplates() {
        if (!templates) {
            templates = {
                'actionline': getTemplate('actionline'),
                'actionbutton': getTemplate('actionbutton'),
                'charsheet': getTemplate('charsheet')
            };
            //log('Read templates:', templates);
        }
        return templates;
    }

    function onAction(data, textStatus, jqXhr) {
        //log('Success!', data, textStatus, jqXhr);
        handleAction(data);
    }

    function onError(jqXHR, textStatus, errorThrown) {
        log('Error!', jqXHR, textStatus, errorThrown);
    }

    function onStats(data, textStatus, jqXhr) {
        var hero;
        if (!data['data'] || !data['data']['hero']) return;
        hero = data['data']['hero']
        //log('Got stats!', data, textStatus, jqXhr);
        updateCharsheet(hero);
    }

    function onMetadata(data, textStatus, jqXhr) {
        if (data) {
            metadata = $.extend(true, {}, data, metadata);
        }
        if (metadata['actions']) {
            updateTaskbar(metadata['actions']);
        }
    }

    function ajaxAction(cmd, successFn, url, data) {
        data = data || {};
        if (!data['format']) data['format'] = 'json';
        if (!url) {
            url = gameKey ? gameUrl + gameKey + '/' : gameUrl;
        }
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
            //log('Removing action:', id, el);
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

    function getActionHtml(data) {
        var line, cls, info = '', extraInfo = '', extraCls = '';
        cls = getActionClass(data['command']);
        if (!data['channel_message']) {
            cls += ' ownAction';
        }
        log('data', data);

        // Gather extra info.
        // FIXME: Need to be dynamic per game.
        if (data && data['data'] && data['data']['hurt_in_fight']) {
            extraInfo = 'Hurt: -' + data['data']['hurt_in_fight'];
            extraCls = 'hurtInfo';
        } else if (data && data['data'] && data['data']['hurt_by_trap']) {
            extraInfo = 'Hurt: -' + data['data']['hurt_by_trap'];
            extraCls = 'hurtInfo';
        } else if (data && data['data'] && data['data']['rested']) {
            extraInfo = 'Rest: +' + data['data']['rested'];
            extraCls = 'restInfo';
        } else if (data && data['data'] && data['data']['loot']) {
            extraInfo = 'Loot: ' + data['data']['loot']
            extraCls = 'lootInfo';
        } else if (data && data['data'] && data['data']['hero'] && data['data']['hero']['level']) {
            extraInfo = 'Level: ' + data['data']['hero']['level']
            extraCls = 'levelInfo';
        }
        if (extraInfo) {
            extraInfo = '<span class="extraInfo ' + extraCls + '"> ' + extraInfo + '</span>';
        }

        // Create html
        line = $.tache(getTemplates().actionline, { 'line': data.message, 'id': data.id, cls: cls, extraInfo: extraInfo });
        return line;
    }

    function handleAction(data) {
        var line, cls;
        if ($.inArray(data.id, handledActions) >= 0) {
            //log('Action already handled:', data.id);
            // Highlight line.
            //$('#action_' + data.id).effect("highlight", {}, 500);
            return;
        }

        // Make sure this action isn't handled again.
        handledActions.push(data.id);

        // Update character sheet with new data.
        if (data['data'] && data['data']['hero']) {
            updateCharsheet(data['data']['hero']);
        }

        // Create line html.
        line = getActionHtml(data);

        // Add action to list.
        $('#actionList').append(line);

        // Remove old lines.
        clearLines();
    }

    function updateCharsheet(hero) {
        var stats, valueDiv;
        // Cache reference to hero div.
        if (!heroDiv) {
            heroDiv = $('#heroDiv');
        }

        // Update the hero stats.
        heroStats = $.extend({}, heroStats, hero);

        // Calculate remaining health.
        if (heroStats.hasOwnProperty('health') && heroStats.hasOwnProperty('hurt')) {
            heroStats['current_health'] = (heroStats['health'] - heroStats['hurt']);
            heroStats['hurthealth'] = '' + heroStats['current_health'] + '/' + heroStats['health'];
        }

        // Update div with new data.
        //log('heroDiv:' + heroDiv.html() + '|', 'hero', hero);
        if ($.trim(heroDiv.html()) == '') {
            stats = $.tache(getTemplates().charsheet, heroStats);
            heroDiv.html(stats);
        } else {
            for (var field in heroStats) if (heroStats.hasOwnProperty(field)) {
                //log('field', field, 'value', hero[field]);
                valueDiv = $('#' + field + 'Value');
                if (valueDiv) {
                    valueDiv.html(heroStats[field]);
                }
            }
        }
    }

    function updateTaskbar(actions) {
        var i = 0, taskbar = '', actionbutton = '';
        log('taskbar actions', actions);
        for (i in actions) if (actions.hasOwnProperty(i)) {
            action = actions[i];
            if (action['img'] && (!action['button'] || $.inArray(action['button'], ['active', 'disabled']) >= 0)) {
                actionbutton = $.tache(getTemplates().actionbutton, action);
                taskbar += actionbutton;
            }
        }
        $('#taskbarDiv').html(taskbar);
    }

    function onCreateChannel(data, textStatus, jqXhr) {
        var token;
        log('Channel created:', data, textStatus, jqXhr);
        try {
            channel_token = data['channel_token'];
            channel_client_id = data['channel_client_id'];
            channel = setup_channel(channel_token);
        } catch (e) {
            log('Failed setting up channel.', e);
        }
    }

    function onChannelOpened() {
        //log('Channel was opened');
    }

    function onChannelMessage(message) {
        var data;
        //log('Received message from channel:', message);
        if (message.data) {
            data = $.parseJSON(message.data);
            data['channel_message'] = true;
            handleAction(data);
        }
    }

    function onChannelError(error) {
        log('Received an error from the channel:', error);
    }

    function onChannelClose() {
        log('Channel was closed.');
        // TODO: Request a new client_id and channel.
        ajaxAction('createchannel', onCreateChannel, '/', { client_id: channel_client_id, game: gameKey });
    }

    function setup_channel(token) {
        if (!token) return false;
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

            // Disallow some actions when hero is dead.
            // FIXME: Need to get list of actions from game.
            /*
            if (!heroStats['alive'] || heroStats['hurt'] >= heroStats['health']) {
                if ($.inArray(cmd, ['fight', 'loot', 'rest', 'deeper']) >= 0) {
                    //log('Hero is dead, action not allowed');
                    $('#' + cmd + 'Btn').effect("highlight", { color: 'red' }, 500);
                    return false;
                }
            }
            if (heroStats['alive'] && heroStats['hurt'] == 0 && cmd == 'rest') {
                $('#' + cmd + 'Btn').effect("highlight", { color: 'red' }, 500);
                return false;
            }
            */
            if (metadata['actions'][cmd]) {
                $('#' + cmd + 'Btn').effect("highlight", { color: 'red' }, 500);
                return false;
            }

            ajaxAction(cmd, fn);
        });

        // Update charsheet when clicked.
        $('#heroDiv').live('click', function(event) {
            ajaxAction('stats', onStats);
        });

        // Load stats.
        ajaxAction('stats', onStats);

        // Load game actions
        ajaxAction('metadata', onMetadata);

        // Setup channel if there is a channel token.
        if (window['channel_token']) {
            channel = setup_channel(channel_token);
        }
    }

    // Call setup function.
    setup();

});

