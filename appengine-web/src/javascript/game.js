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
        var cmd = $(this).attr('name'),
            fn = (cmd == 'stats') ? onStats : onAction
            action = '';

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
            // TODO: Loop through all arguments for action.
            // TODO: Needs to reset menu.
            actionargs = [];
            if (!action['menus']) {
                action['menus'] = createMenu(action);
            }
            log('menu:', action['menus']);
            activeMenu = action['menus'][0];
            $('#' + activeMenu['id'] + 'Div').css('visibility', 'visible');
            actionargs.push(activeMenu['key']);
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

    function buildMenuHtml(menu, menuid) {
        var html = '', menuid = menuid || '';
        log('buildMenuHtml', menu, menuid);
        if (menuid) html += '<div id="' + menuid + 'Div" class="drilldown-menu menu-container" style="visibility: hidden">';
        if (!menuid && menu['name']) {
            html += '<a href="#">' + menu['name'] + '</a>';
        }
        if (menuid) {
            html += '<ul id="' + menuid + '">';
        } else {
            html += '<ul>';
        }
        $.each(menu['items'], function(i, item) {
            var li = '', arg = '', leaf = '';
            if ($.type(item) == 'string') {
                li = '<a href="#">' + item + '</a>';
                leaf = ' class="menu-leaf"'
                arg = item;
            } else {
                if (item['items']) {
                    li = buildMenuHtml(item);
                } else {
                    li = '<a href="#">' + item['name'] + '</a>';
                    leaf = ' class="menu-leaf"'
                }
                arg = item['key'];
            }
            //html += '<li><a class="actionArgumentLink" href="#' + arg + '">' + li + '</a></li>';
            html += '<li title="' + arg + '"' + leaf + '>' + li + '</li>';
        });
        html += '</ul>';
        if (menuid) html += '</div>';
        log('Menu html:', html);
        return html;
    }

    function createMenu(action) {
        var menus = [], menu = {}, menuId = '', menuPrefix = 'actionMenu_' + action['key'] + '_',
            menuHtml = '', menuDiv, menuName = '';

        // Build menu html for all arguments
        // TODO: Need to be able to handle multiple list arguments properly.
        $.each(action['arguments'], function(i, item) {
            if (item['type'] == 'list') {
                menu = {
                    'id': menuPrefix + item['key'],
                    'key': item['key'],
                    'name': item['name'],
                };

                // Remove old menu div.
                menuDiv = $('#' + menu['id']);
                if (menuDiv) menuDiv.remove();
                menu['html'] = buildMenuHtml(item, menu['id']);

                // Setup menu
                $('body').append(menu['html']);
                $('#' + menu['id']).dcDrilldown({
                    'speed': 'fast', 'effect': 'slide', 'saveState': false, 'event': 'click',
                    'showCount': false, 'linkType': 'breadcrumb', 'defaultText': menu['name'],
                    'resetText': 'Back'
                });
                menus.push(menu);
            }
        });

        log('menu:', action, menus);
        //$('#' + menuid).position({ my: 'center center', at: 'center center', of: 'body' });
        return menus;
    }

    function setup() {
        // Setup command buttons
        $('.commandBtn').live('click', handleButtonClick);
        $('.dd-wrapper li').live('click', function(ev) {
            var arg = $(this).attr('title');
            log('arg:', arg);
            if (arg) {
                actionargs.push(arg);
            }
            log('arglist:', actionargs);
            if ($(this).hasClass('menu-leaf')) {
                //$('#' + action['menu'] + 'Div').css('visibility', 'visible');
                log('closing menu');
                $('#' + activeMenu['id'] + 'Div').css('visibility', 'hidden');
                console.log($('#' + activeMenu['id']));
                activeMenu = undefined;
                // TODO: Needs to open next argument
            }
            //ev.preventDefault();
            return false;
        });

        // Update charsheet when clicked.
        $('#heroDiv').live('click', function(ev) {
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

