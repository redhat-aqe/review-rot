from unittest import TestCase
import requests
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

from reviewrot.gerritstack import GerritService
import mock_gerrit

PATH = 'reviewrot.gerritstack.'


class GerritTest(TestCase):
    """
    This class represents the Gerrit test cases
    """

    def setUp(self):
        """
        Set up the testing environment.
        """
        self.mock_age = MagicMock()
        self.mock_age.state = 'mock_state'

    @patch(PATH + 'datetime')
    @patch(PATH + 'GerritService.check_request_state')
    @patch(PATH + 'GerritService._call_api')
    @patch(PATH + 'GerritService.get_last_comment')
    @patch(PATH + 'GerritService.has_new_comments')
    @patch(PATH + 'GerritReview')
    @patch(PATH + 'GerritService.get_comments_count')
    @patch(PATH + 'gravatar')
    def test_format_response_no_comment(self,
                                        mock_gravatar,
                                        mock_comments_count,
                                        mock_GerritReview,
                                        mock_has_new_comments,
                                        mock_get_last_comment,
                                        mock_call_api,
                                        mock_check_request_state,
                                        mock_datetime):
        """
        Tests 'format_response' function where:
            * check_request_state returns True
            * show_last_comment is None
            * owner.get('email') returns None
        """
        # Set up mock return values and side effects
        mock_datetime.strptime.return_value = 'mock_date'
        mock_check_request_state.return_value = True
        mock_call_api.return_value = 'mock_comments_response'
        mock_get_last_comment.return_value = None
        mock_comments_count.return_value = 1
        mock_GerritReview.return_value = '1'
        mock_decoded_response = mock_gerrit.mock_decoded_response_no_email()
        mock_gravatar.return_value = 'mock_image'

        # Call function
        response = GerritService().format_response(
            decoded_responses=mock_decoded_response,
            age=self.mock_age,
            show_last_comment=None
        )

        # Validate function calls and response
        mock_gravatar.assert_called_with('mock_email')
        mock_datetime.strptime.assert_called_with('mock_d', "%Y-%m-%d %H:%M:%S.%f")
        mock_check_request_state.assert_called_with('mock_date', self.mock_age)
        mock_call_api.assert_called_with('None/changes/mock_id/comments')
        mock_get_last_comment.assert_called_with('mock_comments_response')
        mock_has_new_comments.assert_not_called()
        mock_GerritReview.assert_called_with(
            user='mock_username',
            title='mock_subject',
            url='None/mock_number',
            time='mock_date',
            updated_time='mock_date',
            comments=1,
            last_comment=None,
            project_name='mock_project',
            image='mock_image'
        )
        self.assertEqual(['1'], response)

    @patch(PATH + 'datetime')
    @patch(PATH + 'GerritService.check_request_state')
    @patch(PATH + 'GerritService._call_api')
    @patch(PATH + 'GerritService.get_last_comment')
    @patch(PATH + 'GerritService.has_new_comments')
    @patch(PATH + 'GerritReview')
    @patch(PATH + 'GerritService.get_comments_count')
    def test_format_response_with_age(self,
                                      mock_comments_count,
                                      mock_GerritReview,
                                      mock_has_new_comments,
                                      mock_get_last_comment,
                                      mock_call_api,
                                      mock_check_request_state,
                                      mock_datetime):
        """
        Tests 'format_response' function where:
            * check_request_state returns False
            * show_last_comment is None
            * owner.get('email') returns None
        """
        # Set up mock return values and side effects
        mock_datetime.strptime.return_value = 'mock_date'
        mock_check_request_state.return_value = False
        mock_call_api.return_value = 'mock_comments_response'
        mock_get_last_comment.return_value = None
        mock_decoded_response = mock_gerrit.mock_decoded_response_no_email()

        # Call function
        response = GerritService().format_response(
            decoded_responses=mock_decoded_response,
            age=self.mock_age,
            show_last_comment=None
        )

        # Validate function calls and response
        mock_datetime.strptime.assert_called_with('mock_d', "%Y-%m-%d %H:%M:%S.%f")
        mock_check_request_state.assert_called_with('mock_date', self.mock_age)
        mock_call_api.assert_called_with('None/changes/mock_id/comments')
        mock_has_new_comments.assert_not_called()
        mock_comments_count.assert_not_called()
        mock_GerritReview.assert_not_called()
        self.assertEqual([], response)

    @patch(PATH + 'datetime')
    @patch(PATH + 'GerritService.check_request_state')
    @patch(PATH + 'GerritService._call_api')
    @patch(PATH + 'GerritService.get_last_comment')
    @patch(PATH + 'GerritService.has_new_comments')
    @patch(PATH + 'GerritReview')
    @patch(PATH + 'GerritService.get_comments_count')
    def test_format_response_with_last_comment(self,
                                               mock_comments_count,
                                               mock_GerritReview,
                                               mock_has_new_comments,
                                               mock_get_last_comment,
                                               mock_call_api,
                                               mock_check_request_state,
                                               mock_datetime):
        """
        Tests 'format_response' function where:
            * check_request_state returns True
            * show_last_comment is True
            * owner.get('email') returns something
        """
        # Set up mock return values and side effects
        mock_datetime.strptime.return_value = 'mock_date'
        mock_check_request_state.return_value = True
        mock_call_api.return_value = 'mock_comments_response'
        mock_last_comment = MagicMock()
        mock_last_comment.created_at = 'mock_date'
        mock_get_last_comment.return_value = mock_last_comment
        mock_comments_count.return_value = 1
        mock_GerritReview.return_value = '1'
        mock_decoded_response = mock_gerrit.mock_decoded_response_with_email()

        # Call function
        response = GerritService().format_response(
            decoded_responses=mock_decoded_response,
            age=self.mock_age,
            show_last_comment=True
        )

        # Validate function calls and response
        mock_datetime.strptime.assert_called_with('mock_d', "%Y-%m-%d %H:%M:%S.%f")
        mock_check_request_state.assert_called_with('mock_date', self.mock_age)
        mock_call_api.assert_called_with('None/changes/mock_id/comments')
        mock_has_new_comments.assert_called_with(
            'mock_date',
            True
        )
        mock_get_last_comment.assert_called_with('mock_comments_response')
        mock_GerritReview.assert_not_called()
        self.assertEqual([], response)

    @patch(PATH + 'LastComment')
    @patch(PATH + 'datetime')
    def test_get_last_comment(self,
                              mock_datetime,
                              mock_LastComment):
        """
        Tests 'get_last_comment' function
        """
        # Set up mock return values and side effects
        mock_comments_response = mock_gerrit.mock_comments_response()
        mock_datetime.strptime.return_value = 'mock_date'
        mock_comment = MagicMock()
        mock_comment.created_at = 'mock_date'
        mock_LastComment.return_value = mock_comment

        # Call function
        response = GerritService().get_last_comment(
            comments_response=mock_comments_response
        )

        # Validate function calls and response
        mock_datetime.strptime.assert_called_with(
            'mock_upd',
            "%Y-%m-%d %H:%M:%S.%f"
        )
        mock_LastComment.assert_called_with(
            author='mock_username',
            body='mock_message',
            created_at='mock_date'
        )
        self.assertEqual(mock_comment, response)

    @patch(PATH + 'GerritService._call_api')
    def test_repo_exists_successful(self,
                                    mock_call_api):
        """
        Tests 'check_repo_exists' function where there are no errors
        """
        # Set up mock return values and side effects
        mock_call_api.return_value = True

        # Call function
        response = GerritService().check_repo_exists(
            repo_name='mock_repo',
            ssl_verify=True
        )

        # Validate function calls and response
        mock_call_api.assert_called_with(
            url='None/projects/mock_repo',
            ssl_verify=True
        )
        self.assertEqual(True, response)

    @patch(PATH + 'GerritService._call_api')
    def test_repo_exists_failure(self,
                                 mock_call_api):
        """
        Tests 'check_repo_exists' function where there are errors
        """
        # Set up mock return values and side effects
        mock_call_api.side_effect = requests.exceptions.HTTPError

        # Call function
        with self.assertRaises(ValueError):
            GerritService().check_repo_exists(
                repo_name='mock_repo',
                ssl_verify=True
            )

        mock_call_api.assert_called_with(
            url='None/projects/mock_repo',
            ssl_verify=True
        )

    @patch(PATH + 'GerritService.get_response')
    @patch(PATH + 'GerritService.check_repo_exists')
    @patch(PATH + 'GerritService._call_api')
    @patch(PATH + 'GerritService.format_response')
    def test_request_reviews_host_exists(self,
                                         mock_format_response,
                                         mock_call_api,
                                         mock_check_repo_exists,
                                         mock_get_response):
        """
        Tests 'get_reviews' function where:
            * Self.url != host
            * Repos exist
        """
        # Set up mock return values and side effects
        mock_get_response.return_value = 'mock_host_exists'
        mock_check_repo_exists.return_value = True
        mock_call_api.return_value = 'mock_review_response'
        mock_format_response.return_value = 'Successful Call!'

        # Call function
        response = GerritService().request_reviews(
            host='mock_host',
            repo_name='mock_repo'
        )

        # Validate function calls and response
        mock_get_response.assert_called_with(
            method='HEAD',
            url='mock_host',
            ssl_verify=True
        )
        mock_check_repo_exists.assert_called_with(
            'mock_repo',
            True
        )
        mock_call_api.assert_called_with(
            url='mock_host/changes/?q=project:'
                'mock_repo+status:open&o=DETAILED_ACCOUNTS',
            ssl_verify=True
        )
        mock_format_response.assert_called_with(
            'mock_review_response',
            None,
            None
        )
        self.assertEqual('Successful Call!', response)

    @patch(PATH + 'GerritService.get_response')
    @patch(PATH + 'GerritService.check_repo_exists')
    @patch(PATH + 'GerritService._call_api')
    @patch(PATH + 'GerritService.format_response')
    def test_request_reviews_no_host(self,
                                     mock_format_response,
                                     mock_call_api,
                                     mock_check_repo_exists,
                                     mock_get_response):
        """
        Tests 'get_reviews' function where:
            * Self.url == host
            * Repos exist
        """
        # Set up mock return values and side effects
        mock_check_repo_exists.return_value = True
        mock_call_api.return_value = 'mock_review_response'
        mock_format_response.return_value = 'Successful Call!'
        service = GerritService()
        service.host_exists = True

        # Call function
        response = service.request_reviews(
            host=None,
            repo_name='mock_repo'
        )

        # Validate function calls and response
        mock_get_response.assert_not_called()
        mock_check_repo_exists.assert_called_with(
            'mock_repo',
            True
        )
        mock_call_api.assert_called_with(
            url='None/changes/?q=project:mock_repo+status:open&o=DETAILED_ACCOUNTS',
            ssl_verify=True
        )
        mock_format_response.assert_called_with(
            'mock_review_response',
            None,
            None
        )
        self.assertEqual('Successful Call!', response)

    @patch(PATH + 'GerritService.get_response')
    @patch(PATH + 'GerritService.check_repo_exists')
    @patch(PATH + 'GerritService._call_api')
    @patch(PATH + 'GerritService.format_response')
    def test_request_reviews_no_repos(self,
                                      mock_format_response,
                                      mock_call_api,
                                      mock_check_repo_exists,
                                      mock_get_response):
        """
        Tests 'get_reviews' function where:
            * Self.url == host
            * Repos don't exists
        """
        # Set up mock return values and side effects
        mock_check_repo_exists.return_value = None
        mock_call_api.return_value = 'mock_review_response'
        mock_format_response.return_value = 'Successful Call!'
        service = GerritService()
        service.host_exists = True

        # Call function
        response = service.request_reviews(
            host=None,
            repo_name='mock_repo'
        )

        # Validate function calls and response
        mock_get_response.assert_not_called()
        mock_check_repo_exists.assert_called_with(
            'mock_repo',
            True
        )
        mock_call_api.assert_not_called()
        mock_format_response.assert_not_called()
        self.assertEqual(None, response)

    def test_get_comments_count(self):
        """
        Tests 'get_comments_count' function
        """
        # Set up mock return values and side effects
        mock_comments_response = {'/COMMIT_MSG': '', 'MOCK': 'MOCK'}

        # Call function
        response = GerritService().get_comments_count(
            comments_response=mock_comments_response
        )

        # Validate function calls and response
        self.assertEqual(response, 4)
