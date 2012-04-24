$(document).ready(function() {
    var gameUrl = '/api/',
        MAX_LINES = 50,
        templates,
        metadata = {},
        channel,
        handledActions = [],
        heroStats = {},
        heroDiv,
        actionargs = [],
        activeMenu;

    // Log if console.log exists and we are running on localhost
    function log() {
        if (window.console && console.log && document.domain == 'localhost') {
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
                'charsheet': getTemplate('charsheet'),
                'extrainfo': getTemplate('extrainfo')
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

    function updateMetadata(data) {
        log('updateMetadata()', data);
        // Update the metadata
        metadata = $.extend(true, {}, metadata, data);

        // Keep list of disabled actions for easy access.
        metadata['_disabled_actions'] = [];
        $.each(metadata['actions'], function(i, item) {
            if (item['button'] == 'disabled') {
                metadata['_disabled_actions'].push(item['key']);
            }
        });
        log('updated metadata:', metadata);
    }

    function getAction(name) {
        var action;
        $.each(metadata['actions'], function(i, item) {
            if (item['key'] == name) {
                action = item;
            }
        });
        return action;
    }

    function onMetadata(data, textStatus, jqXhr) {
        if (data) {
            updateMetadata(data);
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
        var line, cls, info = '', extraInfo = '', extraCls = '', extraInfoTmpl = '';
        cls = getActionClass(data['command']);
        if (!data['channel_message']) {
            cls += ' ownAction';
        }
        log('data', data);

        // Gather extra info.
        if (data && data['data'] && data['data']['extra_info']) {
            $.each(data['data']['extra_info'], function(k, v) {
                var extraInfoMetadata, values = { 'value': v, cls: '' };
                if (v && metadata['extra_info'] && metadata['extra_info'][k]) {
                    values = $.extend(values, metadata['extra_info'][k]);
                    log('extrainfo template:', getTemplates().extrainfo, values);
                    extraInfo += $.tache(getTemplates().extrainfo, values);
                }
            });
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

        // Update taskbar if it has changed.
        if (data['metadata']) {
            log('metadata', data['metadata']);
            updateMetadata(data['metadata'])
            if (data['metadata']['actions']) {
                updateTaskbar(metadata['actions']);
            }
        }

        // Create line html.
        line = getActionHtml(data);

        // Add action to list.
        $('#actionList').append(line);

        // Remove old lines.
        clearLines();
    }

    function handleButtonClick(event) {
        var cmd = $(this).attr('name'), action = '', argumenttree;
            fn = (cmd == 'stats') ? onStats : onAction,

        log('cmd', cmd, 'metadata actions:', metadata['actions']);
        // Check if action is disabled.
        // TODO: Possibly move this to own button listener.
        if ($.inArray(cmd, metadata['_disabled_actions']) >= 0) {
            $('#' + cmd + 'Div').effect("highlight", { color: 'red' }, 500);
            return false;
        }

        // Check arguments
        action = getAction(cmd);
        if (action && action['arguments']) {
            argumenttree = $.extend(true, [], action['arguments']);
            buildArgumentMenu(argumenttree, action, {});
        } else {
            ajaxAction(cmd, fn);
        }
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

    // TODO: Save each dialog, or remove it when finished.
    // TODO: Some design.
    function buildArgumentMenu(argumenttree, action, arglist) {
        var arg;
        // If argument tree is empty, call action with arglist.
        if (!argumenttree || argumenttree.length == 0) {
            log('Argument tree is empty.', argumenttree, action, arglist);
            ajaxAction(action['key'], onAction, undefined, arglist);
            return true;
        }
        arg = argumenttree[0];
        if (arg['type'] == 'list') {
            createDialogMenu(arg, argumenttree, action, arglist);
        } else if (arg['type'] == 'input') {
            createDialogInput(arg, argumenttree, action, arglist);
        }
        // actionargs.push(arg);
    }

    function createDialogMenu(arg, argumenttree, action, arglist) {
        var html = '', $dialog = {};
        //argumenttree.shift();
        if (arg['description']) {
            html += '<p>' + arg['description'] + '</p>';
        }

        html += '<ul class="argumentMenu">';
        $.each(arg['items'], function(i, item) {
            if ($.type(item) == 'string') {
                html += '<li class="argumentMenuItem" title="' + item + '"><a href="#' + item + '">' + item + '</a></li>';
            } else {
                html += '<li class="argumentMenuItem" title="' + item['key'] + '"><a href="#' + item['key'] + '">' + item['name'] + '</a></li>';
            }
        });
        html += '</ul>';

        // TODO: Save dialog in action item.
        $dialog = $('<div></div>').html(html).dialog({
            draggable: false, width: 240, modal: true, resizable: false,
            title: arg['name'], autoOpen: false, dialogClass: 'argumentDialog'
        });

        $($dialog).on('click', '.argumentMenuItem', function(ev) {
            var item = {}, items = [], value = '';

            // Add given value to argument list.
            value = $(this).attr('title');
            //arglist.push({ 'key': arg['key'], 'value': value });
            arglist[arg['key']] = value;
            log('key:', arg['key'], 'value:', value, 'arglist:', arglist, 'tree', argumenttree);

            // Update argument tree
            items = $.grep(arg['items'], function(itm, idx) {
                if ($.type(itm) != 'string' && itm['key'] == value && itm['items']) {
                    return true;
                } else {
                    return false;
                }
            });
            if (items.length > 0) {
                argumenttree[0] = items[0];
            } else {
                argumenttree.shift();
            }

            // Close dialog
            $dialog.dialog('destroy');
            $dialog.remove();

            // Build next dialog in tree, or send action if empty.
            buildArgumentMenu(argumenttree, action, arglist);
        });

        $dialog.dialog('open');
    }

    function createDialogInput(arg, argumenttree, action, arglist) {
        var html = '', $dialog = {};
        // Handle sub-trees
        if (arg['description']) {
            html += '<p>' + arg['description'] + '</p>';
        }
        html += '<input type="input" class="argumentInput" name="argumentInput_' + arg['key'] + '" value="" />';

        // TODO: Handle enter/ok button click -> call menuHandler

        $dialog = $('<div></div>').html(html).dialog({
            draggable: false, width: 240, modal: true, resizable: false,
            title: arg['name'], dialogClass: 'argumentDialog',
            buttons: { 
                "Ok": function (ev) {
                    var item = {}, value = '';

                    // Add given value to argument list.
                    value = $(this).children('input').val();
                    //arglist.push({ 'key': arg['key'], 'value': value });
                    arglist[arg['key']] = value;
                    log('key:', arg['key'], 'value:', value, 'arglist:', arglist, 'tree', argumenttree);

                    // Update argument tree
                    if (arg['subtree']) {
                        argumenttree[0] = arg['subtree'];
                    } else {
                        argumenttree.shift();
                    }

                    // Close dialog
                    //$dialog.dialog('close');
                    $dialog.dialog('destroy');
                    $dialog.remove();

                    // Build next dialog in tree, or send action if empty.
                    buildArgumentMenu(argumenttree, action, arglist);
                }
            }
        });
    }

    function setup() {
        // Setup command buttons
        $(document).on('click', '.commandBtn', handleButtonClick);

        // Update charsheet when clicked.
        $(document).on('click', '#heroDiv', function(ev) {
            ajaxAction('stats', onStats);
        });

        // Load game actions
        ajaxAction('metadata', onMetadata);

        // Load stats.
        ajaxAction('stats', onStats);

        // Setup channel if there is a channel token.
        if (window['channel_token']) {
            channel = setup_channel(channel_token);
        }
    }

    // Call setup function.
    setup();

});

