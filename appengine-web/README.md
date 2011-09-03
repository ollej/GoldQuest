Gold Quest Appengine Web App
============================

This is the appengine web app version of Gold Quest.

It also provides a simple API to play the game.

The Gold Quest web game is available on the following URL:

    http://gold-quest.appspot.com/

Gold Quest
----------
Gold Quest is a simple multi-user co-op text based dungeon quest game with multiple client options.

The main Gold Quest code is available here:

    https://github.com/ollej/GoldQuest/

Gold Quest Web
--------------
The web version of Gold Quest allows players from anywhere to easily play Gold Quest
by simpling clicking on buttons for each action.

There is also a list of the top 10 heroes of all time available.

Gold Quest Widget
-----------------

The Gold Quest Widget is a widget that can be inserted into any web page to
allow the visitors to the site to play the game.

Currently all players on all sites will play the same hero, but there are plans to
allow site owners to authenticate and create their own hero. This would allow for
co-op within the site and friendly rivalry between sites.

### Installation ###
The only thing you need to do is to place the following HTML code somewhere on your site.

    <iframe src="http://gold-quest.appspot.com/game.html" 
            id="goldquestIframe" 
            width="230" height="380" 
            frameborder="0" scrolling="no" />

Gold Quest API
--------------

The API doesn't require any authentication for any of the current requests.

Responses will be returned based on given Accept header, either text/plain,
application/xml or text/javascript

If the request was successful, the HTTP Response Status will be 200, otherwise
a proper failure status is sent.

### API URL ###
The main URL for the API is the following:

    http://gold-quest.appspot.com/api/

### Example Response ###
In text/plain mode, only the message will be returned in the body. Otherwise all messages
will contain the following data:

    message - String, text message describing the result of the action.
    success - Boolean, true if the request was a success.
    data - Object, additional data depending on request type.

### Routes ###
The following API requests are available.

#### /api/fight ####
Makes the hero look for a monster and fight it to the death.

 * hero - Object, the new values of the hero
   * hurt - Integer, amount of hurt the hero has received.
   * kills - Integer, the number of monsters the hero has killed.
   * alive - Boolean, true if the hero is still alive.
 * monster - Object, data about the monster that was fought.
   * name - String, name of the monster the hero fought.
   * hurt - Integer, amount of hurt the hero inflicted on the monster.
   * strength - Integer, the strength of the monster.
   * health - Integer, the original health of the monster.
   * boss - Boolean, true if this was a boss.
   * count - Integer, number of monsters in this encounter.

#### /api/loot ####
The hero will try to loot killed monsters for loot.

 * gold - The amount of gold the hero found.
 * hero - Object, the new values of the hero
   * gold - Integer, the amount of gold the hero has looted.

#### /api/deeper ####
Sends the hero one level deeper into the dungeon (and increases the hero's level as well).

 * level - Integer, the level the hero is on in the dungeon.

#### /api/rest ####
If the hero has been hurt, a small amount of health is restored.

 * hero - Object, the new values of the hero
   * health - The maximum health of the hero.
   * hurt - Integer, amount of hurt the hero has received.
   * alive - Boolean, true if the hero is still alive.

#### /api/stats ####
Returns information about the hero's stats.

 * hero - Object, the new values of the hero
   * strength - The strength of the hero.
   * health - The maximum health of the hero.
   * hurt - Integer, amount of hurt the hero has received.
   * gold - Integer, the amount of gold the hero has looted.
   * kills - Integer, the number of monsters the hero has killed.
   * level - Integer, the level the hero is on in the dungeon.
   * alive - Boolean, true if the hero is still alive.

#### /api/reroll ####
Rerolls a new character if the current hero has died.

 * hero - Object, the new values of the hero
   * strength - The strength of the hero.
   * health - The maximum health of the hero.
   * hurt - Integer, amount of hurt the hero has received.
   * gold - Integer, the amount of gold the hero has looted.
   * kills - Integer, the number of monsters the hero has killed.
   * level - Integer, the level the hero is on in the dungeon.
   * alive - Boolean, true if the hero is still alive.

