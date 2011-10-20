$(document).ready(function() {
    var appIconTmpl = $('#appiconTemplate').html();

    function onAppList(data, textStatus, jqXhr) {
        if (!data) return;
        $.each(data['games'], function(i, item) {
            var html, gameName;
            if (item == 'goldapps') return;
            //html = '<img src="images/icon-' + item + '.png" class="appIcon" alt="' + item + '" title="' + item + '" />';
            html = $.tache(appIconTmpl, { 'gameKey': item, 'gameName': item });
            $('#appsDiv').append(html);
        });
    }

    $.ajax({
        url: '/api/applist',
        data: {},
        headers: { 
            'Accept': 'application/json',
            'Content-Type': 'text/plain; charset=utf-8'
        },
        dataType: 'json',
        success: onAppList
    });

    $('.appIcon').live('click', function(ev) {
        var game = $(ev.target).attr('title');
        if (game) {
            document.location = '?game=' + game;
        }
        return false;
    });
});

