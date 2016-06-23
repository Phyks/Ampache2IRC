#!/usr/bin/env python
"""
IRC bot to track currently played songs on Ampache.

Code under MIT license.
"""
import ssl

import feedparser
import irc.bot
import irc.connection

import config

from haikunator import Haikunator


class Ampache2IRC(irc.bot.SingleServerIRCBot):
    """
    Main bot class
    """
    def __init__(self):
        self.last_seen = None
        if not config.use_ssl:
            irc.bot.SingleServerIRCBot.__init__(self, [(config.server,
                                                        config.port)],
                                                config.nick,
                                                config.desc)
        else:
            self.ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            irc.bot.SingleServerIRCBot.__init__(
                self, [(config.server, config.port)],
                config.nick,
                config.desc,
                connect_factory=self.ssl_factory)

    def refresh_feed(self, serv):
        """Refresh Ampache played RSS feed"""
        d = feedparser.parse("%s/rss.php?type=recently_played" %
                             (config.ampache_URL,))
        for entry in d.entries:
            if(self.last_seen is None or
               entry.published_parsed > self.last_seen):
                haikunator = Haikunator(entry.comments
                                        .replace(config.ampache_URL, "")
                                        .strip("/"))
                serv.privmsg(config.channel,
                             "%c%02d %s (%s)" %
                             (3, 14, entry.title,
                              haikunator.haikunate(token_length=0)))
                self.last_seen = entry.published_parsed

    def on_welcome(self, serv, ev):
        """Upon server connection, handles nickserv"""
        if config.password != "":
            serv.privmsg("nickserv", "identify %s" % (config.password,))
        serv.join(config.channel)
        # Refresh feed every 10 seconds
        self.connection.execute_every(10, self.refresh_feed, (serv,))

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        pass

    def on_pubmsg(self, serv, ev):
        """Handles the messages on the chan"""
        pass

    def close(self):
        """Exits nicely"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


if __name__ == '__main__':
    try:
        with Ampache2IRC() as bot:
            bot.start()
    except KeyboardInterrupt:
        pass
