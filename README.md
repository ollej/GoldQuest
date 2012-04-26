GoldQuest
=========

A simple multi-user co-op text based dungeon quest game with multiple client options.

Playing Gold Quest
------------------

The object of Gold Quest is to collect as much gold as possible while traversing a dungeon filled with monsters. All players control the same hero and will see the results of the actions by all other players.

Available actions: fight, loot, deeper, rest, stats, reroll

License
-------

Gold Quest is released under The MIT License. See LICENSE file for more details.

Requirements
------------

To run:
 * PyYAML
 * nose
 * simplejson

For development:
 * fabric
 * minimock
 * Google Closure Compiler
 * Google AppEngine SDK

Installation
------------
 * Install the required Python libraries using easy_install.
 * Create a symbolic link to GoldFrame games in appengine-web:
    $ cd appengine-web/src/ && ln -s ../../src GoldFrame
 * Run fabric script to compile javascript
    $ fab compile


Multiple Clients
----------------

There are several different ways of playing Gold Quest, as there are a number of different game clients available. Some clients are stand-alone while others share the same database.

### Gold Quest Web ###

The web version of Gold Quest allows players from anywhere to easily play Gold Quest by simpling clicking on buttons for each action.

There is also a list of the top 10 heroes of all time on the web version available.

The Gold Quest Web basically just uses the Gold Quest Widget, but also has some extra options.

Visit Gold Quest Web here: http://gold-quest.appspot.com

### Gold Quest Mobile ###
There is a version of Gold Quest that is optimized to run on mobile devices such as iPhone and Android. Just visit the page linked below and bookmark it to your homepage to play on the go.

Visit Gold Quest Mobile:

http://gold-quest.appspot.com/mobile.html

### Gold Quest Android App ###
For Android users there is a downloadable app to easily play the game.

Download the Gold Quest Android App from Android Market:

https://market.android.com/details?id=com.jxdevelopment.goldquest

### Gold Quest Widget ###

The Gold Quest Widget is a widget that can be installed on any web page. It uses the Gold Quest API to connect to the Gold Quest in the cloud.

### Gold Quest Telnet Server ###

The Gold Quest code also contains a telnet server which can be set up to allow players to connect to the game via a telnet client.

There is currently no telnet server publically available.

#### Usage: ####

    twistd gqtelnetserver.py

### Gold Quest Twitter ###

It is possible to play Gold Quest by mentioning the different commands to the Twitter account @Gold_Quest and the result of the action will be tweeted out.

The Twitter version is currently a stand-alone game with its own hero.

http://twitter.com/#!/Gold_Quest

To run the Twitter version you need to use the Twippy Twitter bot which has a Gold Quest plugin.

https://github.com/ollej/Twippy

### Gold Quest Command Line ###

There is a command line version of Gold Quest available that allows players to play the game at home using a command line interface.

The command-line interface is also stand-alone, meaning only the person running the client will control the hero.

#### Usage: ####

    python CommandLine.py

### Gold Quest Chat ###

Gold Quest is also available to be played in a chat environment. This is done via a plugin to the chat bot Shoutbridge. This supports Jabber/XMPP clients as well as UBB.threads forum system shoutbox.

http://github.com/ollej/shoutbridge

