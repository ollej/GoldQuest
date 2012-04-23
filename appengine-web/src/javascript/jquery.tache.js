/* 
 * Smallest mustache template implementation
 *
 * Nic Ferrier, WooMedia inc, nic@woome.com
 *
 * This mustache has no syntax at all except the interpolation of
 * variables.  As such it is useful where string concatentation might
 * otherwise be used and nowhere else.
 *
 * Example:
 *
 *   jQuery.tache('<a href="{{url}}" title="{{name}}">{{name}}</a>', {
 *            url: "http://github.com/woome/tache",
 *            name="tache - the simple mustache template"
 *            }
 *         );
 */

jQuery.tache = function (template, ctx) {
    var t = template;
    // Original regexp: /{{(.*?)}}/, 
                // /\[\[\s*(.*?)\s*\]\]/, 
    while (true) {
        var res = t.replace(
            /{{\s*(.*?)\s*}}/, 
            function (matched, p1, offset, src) { return ctx[p1]; }
        );
        if (res == t) {
            break;
        }
        t = res;
    }
    return t;
};
