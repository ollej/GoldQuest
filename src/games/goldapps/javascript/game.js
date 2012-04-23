/*jslint browser: true, white: true */
/*global $ */

$(document).ready(function () {
    'use strict';
    var appIconTmpl = $('#appiconTemplate').html();

    function onAppList(data, textStatus, jqXhr) {
        if (!data) {
            return;
        }
        $.each(data.games, function (i, item) {
            var html;
            if (item === 'goldapps') {
                return;
            }
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

    $('.appIcon').live('click', function (ev) {
        var game = $(ev.target).attr('title');
        if (game) {
            document.location = '?game=' + game;
        }
        return false;
    });
});

