"""ircstack module."""
import logging
import socket
import sys
import time

log = logging.getLogger(__name__)


class IRC:
    """IRC component used to connect to channel and send message to channel."""

    def __init__(self, config, channels):
        """TODO: docstring goes here."""
        try:
            self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            log.exception("Error creating socket: %s", e)
            sys.exit(1)

        self.irc.settimeout(10)
        self.server = config["server"]
        self.port = config["port"]
        self.channels = channels
        self.nick = "review_rot_bot"

    def connect(self):
        """Connects the bot to the IRC channel."""
        log.debug("Connecting to server")

        try:
            self.irc.connect((self.server, self.port))
        except socket.gaierror as e:
            log.exception("Address-related error connecting to server: %s", e)
            sys.exit(1)
        except socket.error as e:
            log.exception("Connection error: %s", e)
            sys.exit(1)

        for channel in self.channels:
            log.debug("Joining channel %s" % channel)
            try:
                self.irc.send(
                    "USER {0} {0} {0} {0}\r\n".format(self.nick).encode("utf-8")
                )
                self.irc.send("NICK {}\r\n".format(self.nick).encode("utf-8"))
                self.irc.send("JOIN {}\r\n".format(channel).encode("utf-8"))
            except socket.error as e:
                log.exception("Error while sending data to server: %s", e)
                sys.exit(1)

        # IRC servers use ping for authorization
        try:
            buffer = self.irc.recv(1024)
        except socket.error as e:
            log.exception("Error while receiving data from server: %s", e)
            sys.exit(1)

        msg = buffer.split()
        if msg[0] == "PING":
            try:
                self.irc.send("PONG {}\r\n".format(msg[1]).encode("utf-8"))
            except socket.error as e:
                log.exception("Error while sending data to server: %s", e)
                sys.exit(1)

        log.debug("Connected")

    def send_msg(self, msg):
        """
        Sends message to IRC channels.

        msg (string): message to be sent to channel
        """
        # remove invalid characters
        msg = msg.replace("\n", "").replace("\r", "")

        for channel in self.channels:
            log.debug("sending msg %s to channel %s", msg, channel)

            try:
                # there are 510 characters
                # maximum allowed for the command and its parameters.
                temp_msg = "PRIVMSG {} :{}".format(channel, msg)[:510]
                self.irc.send("{}\r\n".format(temp_msg).encode("utf-8"))
            except socket.error as e:
                log.exception("Error while sending data to server: %s", e)
                sys.exit(1)
            # to avoid flooding the channel
            time.sleep(0.5)

    def quit(self):
        """Disconnect bot from channel and close the connection."""
        log.debug("closing connection")
        try:
            self.irc.send("QUIT \r\n".encode("utf-8"))
        except socket.error as e:
            log.exception("Error while sending data to server: %s", e)
            sys.exit(1)

        try:
            buffer = self.irc.recv(1024)
            # wait for server to recieve all messages
            # and acknowledge the client quit
            while len(buffer) != 0:
                buffer = self.irc.recv(1024)
        except socket.error as e:
            log.exception("Error while receiving data from server: %s", e)
            sys.exit(1)

        self.irc.close()
