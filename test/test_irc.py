import mock
import unittest
from reviewrot.irc import IRC


class IRCNotificationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_irc = {
            "server": "irc.example.com",
            "port": 12345,
        }
        cls.channels = ["#testChannel"]

    @mock.patch("socket.socket")
    def test_irc_connection(self, mock_socket):

        mock_socket.return_value.recv.return_value = "PING 1"
        irc_bot = IRC(self.config_irc, self.channels)
        irc_bot.connect()
        irc_bot.irc.connect.assert_called_with(('irc.example.com', 12345))

        expected_calls = [
            mock.call(b'USER review_rot_bot review_rot_bot review_rot_bot review_rot_bot\r\n'),
            mock.call(b'NICK review_rot_bot\r\n'),
            mock.call(b'JOIN #testChannel\r\n'),
            mock.call(b'PONG 1\r\n'),
        ]
        irc_bot.irc.send.assert_has_calls(expected_calls)

    @mock.patch("socket.socket")
    def test_irc_send(self, mock_socket):

        irc_bot = IRC(self.config_irc, self.channels)
        irc_bot.send_msg('test msg')
        irc_bot.irc.send.assert_called_with(b'PRIVMSG #testChannel :test msg\r\n')

    @mock.patch("socket.socket")
    def test_irc_quit(self, mock_socket):

        irc_bot = IRC(self.config_irc, self.channels)
        irc_bot.quit()
        irc_bot.irc.send.assert_called_with(b'QUIT \r\n')
        irc_bot.irc.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
