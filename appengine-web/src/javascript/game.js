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
            dataType: 'text',
            success: successFn || onAction,
            error: onError
        });
    }

    function onAction(data, textStatus, jqXhr) {
        if (console && console.log) console.log('Success!', data, textStatus, jqXhr);
        //var line = $("<span class='actionLine'>" + data + "</span>");
        //$('#actionsDiv').append(line);
        //var line = $("<li class='actionLine'>" + data + "</li>");
        var line = $.tache(getTemplates().actionline, { 'line': data });
        $('#actionList').append(line);
    }

    function onError(jqXHR, textStatus, errorThrown) {
        if (console && console.log) console.log('Error!', jqXHR, textStatus, errorThrown);
    }

    function onStats(data, textStatus, jqXhr) {
        if (console && console.log) console.log('Got stats!', data, textStatus, jqXhr);
        var re = /^Stats: /;
        data = data.replace(re, '');
        $('#heroDiv').html(data);
    }

    // Setup command buttons
    $('.commandBtn').live('click', function(event) {
        var cmd = $(this).attr('name'),
            fn = (cmd == 'stats') ? onStats : onAction;
        ajaxAction(cmd, fn);
    });

    $('#heroDiv').live('click', function(event) {
        ajaxAction('stats', onStats);
    });

    ajaxAction('stats', onStats);

});
