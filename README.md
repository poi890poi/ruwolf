Are You A Werewolf?
=============

HTTP chat server for party game 'Are You A Werewolf?'.

History
-------

The game is originally called 'Mafia', created by Dimma Davidoff. Andrew Plotkin,
aka Zarf, later changed the theme to werewolves and Looney Labs published the game
under the title 'Are You A Werewolf?'. I use the name because it's popular and 
also I learned this game by this name.

* [Mafia](http://en.wikipedia.org/wiki/Mafia_%28party_game%29) -- Mafia on Wikipedia
* [Werewolf](http://eblong.com/zarf/werewolf.html) -- Zarf's Werewolf page
* [Are You A Werewolf?](http://www.wunderland.com/LooneyLabs/Werewolf/) -- Are You A Werewolf? offical page


Installation
------------

Python 2.6 is needed to run the scripts.


### Python

Get Python [here](http://www.python.org/download/releases/).

Installation should be easy enough with simple double-click and click next all the way.

### Run Scripts

With Python installed correctly, double-click on '.py' file should execute the
scripts.

Before the server can be run, database must be initialized. Run:

    setup.py


After database is initialized, start chat server by running:

    async.py


Should database is corrupted, reset it by running:

    reset.py (All data will be LOST!)


Usage
-----

Just connect to the server with your usual browser. Browser compatibility is not
tested seriously. Feedback is welcome.