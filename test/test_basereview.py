from unittest import TestCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
try:
    # Python 3 >
    from unittest.mock import patch  # noqa: F401
except ImportError:
    from mock import patch  # noqa: F401
try:
    # Python 3.3 >
    from unittest.mock import MagicMock  # noqa: F401
except ImportError:
    from mock import MagicMock  # noqa: F401

from reviewrot.basereview import BaseReview, BaseService, Age

PATH = 'reviewrot.basereview.'


class BaseServiceTest(TestCase):
    """
    This class represents the BaseService test cases
    """

    def test_check_request_state_newer(self):
        base_service = BaseService()
        # created four hours ago
        now = datetime.now()
        created_at = now - relativedelta(hours=4)

        # include pull request that have been added in the past day
        date = now - relativedelta(days=1)
        age = Age(date=date, state="newer")
        actual = base_service.check_request_state(created_at, age)
        self.assertTrue(actual)

        # include pull request that bave been added in the past 3 hours
        date = now - relativedelta(hours=3)
        age = Age(date=date, state="newer")
        actual = base_service.check_request_state(created_at, age)
        self.assertFalse(actual)

    def test_check_request_state_older(self):
        base_service = BaseService()
        now = datetime.now()
        # created four hours ago
        created_at = now - relativedelta(hours=4)

        # include pull request that are older than 1 day
        date = now - relativedelta(days=1)
        age = Age(date=date, state="older")
        actual = base_service.check_request_state(created_at, age)
        self.assertFalse(actual)

        # include pull request that ale older than 3 hours
        date = now - relativedelta(hours=3)
        age = Age(date=date, state="older")
        actual = base_service.check_request_state(created_at, age)
        self.assertTrue(actual)

    def test_check_request_state_age_is_none(self):
        base_service = BaseService()
        now = datetime.now()
        # created four hours ago
        created_at = now - relativedelta(hours=4)

        # No filtering
        actual = base_service.check_request_state(created_at, None)
        self.assertTrue(actual)

    def test_has_new_comments_none(self):
        """
        Tests 'has_new_comments' function where last_activity and days
        are none
        """
        # Call the function
        response = BaseService().has_new_comments(
            last_activity=None,
            days=None)

        # Assert values were called correctly
        self.assertFalse(response)

    def test_has_new_comments(self):
        """
        Tests 'has_new_comments' function where last_activity and days
        are NOT none
        """
        # Set up mock return values and side effects
        mock_last_activity = datetime.now() - relativedelta(days=599)

        # Call the function
        response = BaseService().has_new_comments(
            last_activity=mock_last_activity,
            days=600)

        # Validate function calls and response
        self.assertTrue(response)

    @patch(PATH + 'json')
    def test_decode_response(self,
                             mock_json):
        """
        Tests '_decode_response' function
        """
        # Set up mock return values and side effects
        mock_response = MagicMock()
        mock_response.encoding = True
        mock_content = MagicMock()
        mock_content.decode.return_value = mock_content
        mock_content.startswith.return_value = True
        mock_response.content.strip.return_value = mock_content
        mock_json.loads.return_value = 'mock_content'

        # Call the function
        response = BaseService()._decode_response(
            mock_response)

        # Validate function calls and response
        self.assertEqual(response, 'mock_content')
        mock_content.decode.assert_called_with(True)
        mock_content.startswith.assert_called_with(")]}\'\n")
        mock_json.loads.assert_called_with(mock_content.__getitem__())

    @patch(PATH + 'json')
    def test_decode_response_valueerror(self,
                                        mock_json):
        """
        Tests '_decode_response' where we have a ValueError
        """
        # Set up mock return values and side effects
        mock_response = MagicMock()
        mock_response.encoding = True
        mock_content = MagicMock()
        mock_content.decode.side_effect = ValueError
        mock_response.content.strip.return_value = mock_content

        # Call the function
        with self.assertRaises(ValueError):
            BaseService()._decode_response(
                mock_response)

        # Validate function calls and response
        mock_content.decode.assert_called_with(True)
        mock_content.startswith.assert_not_called()
        mock_json.loads.assert_not_called()

    @patch(PATH + 'BaseService.get_response')
    @patch(PATH + 'BaseService._decode_response')
    @patch(PATH + 'json')
    def test_call_api(self,
                      mock_json,
                      mock_decode_response,
                      mock_get_response):
        """
        Tests '_call_api'
        """
        # Set up mock return values and side effects
        mock_response = MagicMock()
        mock_response.json.return_value = 'mock_decoded_response'
        mock_get_response.return_value = mock_response

        # Call the function
        response = BaseService()._call_api(
            url='mock_url')

        # Validate function calls and response
        self.assertEqual(response, 'mock_decoded_response')
        mock_response.json.assert_called()
        mock_get_response.assert_called_with(
            'GET', 'mock_url', True)
        mock_decode_response.assert_not_called()

    @patch(PATH + 'BaseService.get_response')
    @patch(PATH + 'BaseService._decode_response')
    @patch(PATH + 'json')
    def test_call_api_valueerror(self,
                                 mock_json,
                                 mock_decode_response,
                                 mock_get_response):
        """
        Tests '_call_api' where we have a ValueError
        """
        # Set up mock return values and side effects
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError
        mock_decode_response.return_value = 'mock_decoded_response'
        mock_get_response.return_value = mock_response

        # Call the function
        response = BaseService()._call_api(
            url='mock_url')

        # Validate function calls and response
        self.assertEqual(response, 'mock_decoded_response')
        mock_response.json.assert_called()
        mock_get_response.assert_called_with(
            'GET', 'mock_url', True)
        mock_decode_response.assert_called_with(mock_response)

    def test_get_response(self):
        """
        Tests 'get_response' function
        """
        # Set up mock return values and side effects
        mock_response = MagicMock()
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        service = BaseService()
        service.header = 'mock_header'
        service.session = mock_session

        # Call the function
        response = service.get_response(
            method='mock_method',
            url='mock_url',
            ssl_verify=True
        )

        # Validate function calls and response
        self.assertEqual(response, mock_response)
        mock_response.raise_for_status.assert_any_call()
        mock_session.request.assert_called_with(
            method='mock_method',
            url='mock_url',
            headers='mock_header',
            verify=True
        )


class BaseReviewTest(TestCase):
    """
    This class represents the BaseReview test cases
    """
    def setUp(self):
        self.mock_base_review = BaseReview()
        self.mock_base_review.user = 'mock_user'
        self.mock_base_review.title = 'mock_title'
        self.mock_base_review.url = 'mock_url'
        self.mock_base_review.time = 'mock_time'

    @patch(PATH + 'datetime')
    def test_format_duration_no_result(self,
                                       mock_datetime):
        """
        Tests 'format_duration' function where we have no result
        """
        # Set up mock return values and side effects
        mock_datetime.datetime.utcnow.return_value = datetime(2018, 2, 2)
        mock_created_at = datetime(2018, 3, 2)

        # Call the function
        response = BaseReview().format_duration(mock_created_at)

        # Validate function calls and response
        self.assertEqual('less than 1 minute', response)

    @patch(PATH + 'datetime')
    def test_format_duration_(self,
                              mock_datetime):
        """
        Tests 'format_duration' function
        """
        # Set up mock return values and side effects
        mock_datetime.datetime.utcnow.return_value = datetime(2018, 2, 2)
        mock_created_at = datetime(2018, 1, 2)

        # Call the function
        response = BaseReview().format_duration(mock_created_at)

        # Validate function calls and response
        self.assertEqual('1 month', response)

    @patch(PATH + 'BaseReview.format_duration')
    def test_format_oneline_one_comment(self,
                                        mock_format_duration):
        """
        Tests '_format_oneline' function with one comment and no last comments
        """
        # Set up mock return values and side effects
        service = self.mock_base_review
        self.mock_base_review.comments = 1
        mock_format_duration.return_value = 'mock_duration'

        # Call the function
        response = service._format_oneline(
            1, 1
        )

        # Validate function calls and response
        self.assertEqual("mock_user filed 'mock_title' "
                         "mock_url mock_duration ago, 1 comment",
                         response)

    @patch(PATH + 'BaseReview.format_duration')
    def test_format_oneline_last_comment(self,
                                         mock_format_duration):
        """
        Tests '_format_oneline' function with more than one
        comment and last comments
        """
        # Set up mock return values and side effects
        service = self.mock_base_review
        self.mock_base_review.comments = 10
        mock_last_comment = MagicMock()
        mock_last_comment.author = 'mock_author'
        mock_last_comment.last_comment.created_at = 'mock_created_at'
        mock_format_duration.return_value = 'mock_duration'
        self.mock_base_review.last_comment = mock_last_comment

        # Call the function
        response = service._format_oneline(
            1, 1
        )

        # Validate function calls and response
        self.assertEqual("mock_user filed 'mock_title' mock_url"
                         " mock_duration ago, 10 comments, "
                         "last comment by mock_author mock_duration ago",
                         response)

    @patch(PATH + 'BaseReview.format_duration')
    def test_format_indented_one_comment(self,
                                         mock_format_duration):
        """
        Tests '_format_indented' function with one comment and no last comments
        """
        # Set up mock return values and side effects
        service = self.mock_base_review
        self.mock_base_review.comments = 1
        mock_format_duration.return_value = 'mock_duration'

        # Call the function
        response = service._format_indented(
            1, 1, False
        )

        # Validate function calls and response
        self.assertEqual("mock_user filed 'mock_title'\n"
                         "\tmock_url\n\tmock_duration ago\n"
                         "\t1 comment",
                         response)

    @patch(PATH + 'BaseReview.format_duration')
    def test_format_indented_last_comment(self,
                                          mock_format_duration):
        """
        Tests '_format_indented' function with more than one
        comment and last comments
        """
        # Set up mock return values and side effects
        service = self.mock_base_review
        self.mock_base_review.comments = 10
        mock_last_comment = MagicMock()
        mock_last_comment.author = 'mock_author'
        mock_last_comment.last_comment.created_at = 'mock_created_at'
        mock_format_duration.return_value = 'mock_duration'
        self.mock_base_review.last_comment = mock_last_comment

        # Call the function
        response = service._format_indented(
            1, 1, True
        )

        # Validate function calls and response
        self.assertEqual("mock_user filed 'mock_title'"
                         "\n\tmock_url\n\tmock_duration"
                         " ago\n\t10 comments, last "
                         "comment by mock_author mock_"
                         "duration ago\n",
                         response)

    @patch(PATH + 'json')
    @patch(PATH + 'BaseReview.__json__')
    def test_format_json(self,
                         mock__json__,
                         mock_json):
        """
        Tests '_format_json' function
        """
        # Set up mock return values and side effects
        mock_json.dumps.return_value = 'mock_format_json'
        mock__json__.return_value = 'mock__json__'

        # Call the function
        response = BaseReview()._format_json(
            1, 2, 3
        )

        # Validate function calls and response
        self.assertEqual(response, 'mock_format_json')
        mock_json.dumps.assert_called_with('mock__json__', indent=2)
        mock__json__.assert_called_with(3)

    @patch(PATH + 'BaseReview.format_duration')
    def test_format_irc_one_comment(self,
                                    mock_format_duration):
        """
        Tests '_format_irc' function with one comment and no last comments
        """
        # Set up mock return values and side effects
        service = self.mock_base_review
        self.mock_base_review.comments = 1
        mock_format_duration.return_value = 'mock_duration'

        # Call the function
        response = service._format_irc()

        # Validate function calls and response
        self.assertEqual("\x02mock_user\x02 filed"
                         " \x02'mock_title'\x02"
                         " \x0312mock_url\x03 mock_duration ago, "
                         "1 comment",
                         response)

    @patch(PATH + 'BaseReview.format_duration')
    def test_format_irc_last_comment(self,
                                     mock_format_duration):
        """
        Tests '_format_irc' function with more than one
        comment and last comments
        """
        # Set up mock return values and side effects
        service = self.mock_base_review
        self.mock_base_review.comments = 10
        mock_last_comment = MagicMock()
        mock_last_comment.author = 'mock_author'
        mock_last_comment.last_comment.created_at = 'mock_created_at'
        mock_format_duration.return_value = 'mock_duration'
        self.mock_base_review.last_comment = mock_last_comment

        # Call the function
        response = service._format_irc()

        # Validate function calls and response
        self.assertEqual("\x02mock_user\x02 filed \x02'mock_title'\x02"
                         " \x0312mock_url\x03 mock_duration ago, 10 comments, "
                         "last comment by \x02mock_author\x02 mock_duration ago",
                         response)
