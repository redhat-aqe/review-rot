"""test pagure."""
import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests
from reviewrot.pagurestack import PagureService

from . import mock_pagure


PATH = "reviewrot.pagurestack."

# Disable logging to avoid messing up test output
logging.disable(logging.CRITICAL)


class PagureTest(TestCase):
    """This class represents the Pagure test cases."""

    def setUp(self):
        """Setting up the testing environment."""
        # Mock Last Comment
        self.mock_last_comment = MagicMock()

        # Mock Datetime
        self.mock_utcfromtimestamp = MagicMock()
        self.mock_utcfromtimestamp.strftime.return_value = "mock_date"

        # Mock Datetime ValueError
        self.mock_utcfromtimestamp_error = MagicMock()
        self.mock_utcfromtimestamp_error.strftime.return_value = "2019-01-05 12:12:12"
        # Mock Age
        self.mock_age = MagicMock()
        self.mock_age.state = "mock_age_state"

    @patch(PATH + "urllib")
    @patch(PATH + "hashlib")
    @patch(PATH + "PagureService._call_api")
    def test_avatar_with_url(self, mock_call_api, mock_hashlib, mock_urllib):
        """Tests '_avatar' function where we have an avatar url."""
        # Set up mock return values and side effects
        mock_response = {"user": {"avatar_url": "dummy_avatar_url"}}
        mock_url_parts = MagicMock()
        mock_url_parts.return_value = "mock_url_parts"
        mock_url_parts.query = "mock_url_parts_query"
        mock_url_query = MagicMock()
        mock_url_query.return_value = "mock_url_query"
        mock_urllib.parse.urlparse.return_value = mock_url_parts
        mock_urllib.parse.parse_qs.return_value = mock_url_query
        mock_urllib.parse.urlencode.return_value = mock_url_query
        mock_urllib.parse.urlunparse.return_value = "dummy_avatar_url"
        mock_call_api.return_value = mock_response

        # Call function
        response = PagureService()._avatar(username="dummy_user")

        # Validate function calls and response
        self.assertEqual(response, "dummy_avatar_url")
        mock_urllib.parse.urlparse.assert_called_with("dummy_avatar_url")
        mock_urllib.parse.parse_qs.assert_called_with("mock_url_parts_query")
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/user/dummy_user", ssl_verify=True
        )
        mock_url_query.update.assert_called_with({"s": 64, "d": "retro"})
        mock_urllib.parse.urlencode.assert_called_with(mock_url_query, doseq=True)
        mock_urllib.parse.urlunparse.assert_called_with(
            mock_url_parts[:4] + (mock_url_query,) + mock_url_parts[5:]
        )
        mock_hashlib.assert_not_called()

    @patch(PATH + "urllib")
    @patch(PATH + "hashlib")
    @patch(PATH + "PagureService._call_api")
    def test_avatar_without_url(self, mock_call_api, mock_hashlib, mock_urllib):
        """Tests '_avatar' function where we don't have an avatar url."""
        # Set up mock return values and side effects
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "mock_idx"
        mock_call_api.return_value = {}
        mock_urllib.parse.urlencode.return_value = "mock_query"
        mock_hashlib.sha256.return_value = mock_hash

        # Call function
        response = PagureService()._avatar(username="dummy_user")

        # Validate function calls and response
        mock_urllib.parse.urlencode.assert_called_with({"s": 64, "d": "retro"})
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/user/dummy_user", ssl_verify=True
        )
        mock_hashlib.sha256.assert_called_once_with(
            b"http://dummy_user.id.fedoraproject.org/"
        )
        self.assertEqual(
            response, "https://seccdn.libravatar.org/avatar/mock_idx?mock_query"
        )
        mock_urllib.parse.urlparse.assert_not_called()
        mock_urllib.parse.parse_qs.assert_not_called()
        mock_urllib.parse.urlunparse.assert_not_called()

    @patch(PATH + "urllib")
    @patch(PATH + "hashlib")
    @patch(PATH + "PagureService._call_api")
    def test_avatar_value_error(self, mock_call_api, mock_hashlib, mock_urllib):
        """Tests '_avatar' function where we get a HTTPError and raise a ValueError."""
        # Set up mock return values and side effects
        mock_call_api.side_effect = requests.exceptions.HTTPError

        # Call function
        with self.assertRaises(ValueError):
            PagureService()._avatar(username="dummy_user")

        # Validate function calls and response
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/user/dummy_user", ssl_verify=True
        )
        mock_urllib.parse.urlencode.assert_not_called()
        mock_hashlib.sha256.assert_not_called()
        mock_urllib.parse.parse_qs.assert_not_called()
        mock_urllib.parse.urlunparse.assert_not_called()

    @patch(PATH + "LastComment")
    @patch(PATH + "datetime")
    def test_last_comment_no_comments(self, mock_datetime, mock_last_comment):
        """Tests 'get_last_comment' with no comments."""
        response = PagureService().get_last_comment(res={"comments": {}})
        mock_datetime.utcfromtimestamp.assert_not_called()
        mock_last_comment.assert_not_called()
        self.assertEqual(None, response)

    @patch(PATH + "LastComment")
    @patch(PATH + "datetime")
    def test_last_comment(self, mock_datetime, mock_last_comment):
        """Tests 'get_last_comment'."""
        # Set up mock return values and side effects
        mock_datetime.utcfromtimestamp.return_value = "mock_date"
        mock_last_comment.return_value = "mock_return_value"

        # Call function
        response = PagureService().get_last_comment(
            res={
                "comments": [
                    {
                        "date_created": "1",
                        "comment": "mock_comment",
                        "user": {"name": "mock_name"},
                    }
                ]
            }
        )

        # Validate function calls and response
        mock_datetime.utcfromtimestamp.assert_called_with(1)
        mock_last_comment.assert_called_with(
            author="mock_name", body="mock_comment", created_at="mock_date"
        )
        self.assertEqual("mock_return_value", response)

    @patch(PATH + "PagureService._call_api")
    @patch(PATH + "PagureService.get_last_comment")
    @patch(PATH + "datetime")
    @patch(PATH + "PagureService.check_request_state")
    @patch(PATH + "PagureService.has_new_comments")
    @patch(PATH + "PagureReview")
    @patch(PATH + "PagureService._avatar")
    def test_request_reviews_with_repo(
        self,
        mock_avatar,
        mock_pagure_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_datetime,
        mock_get_last_comment,
        mock_call_api,
    ):
        """
        Tests 'request_reviews' function with repos.

        and:
            * no last comment,
            * check_request_state returns True
            * no errors,
            * no namespace
        """
        # Set up mock return values and side effects
        mock_check_request_state.return_value = True
        mock_avatar.return_value = "dummy_avatar"
        mock_get_last_comment.return_value = "dummy_last_comment"
        mock_datetime.utcfromtimestamp.return_value = self.mock_utcfromtimestamp
        mock_datetime.strptime.return_value = "mock_strptime_date"
        mock_pagure_review.return_value = "1"
        mock_call_api.return_value = mock_pagure.mock_api_call_return_value()

        # Call function
        response = PagureService().request_reviews(
            user_name="dummy_user", repo_name="dummy_repo"
        )

        # Validate function calls and response
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/dummy_user/dummy_repo/pull-requests",
            ssl_verify=True,
        )
        mock_get_last_comment.assert_called_with(
            mock_call_api.return_value["requests"][0]
        )
        mock_datetime.strptime.assert_called_with("mock_date", "%Y-%m-%d %H:%M:%S.%f")
        mock_has_new_comments.assert_not_called()
        mock_check_request_state.assert_called_with("mock_strptime_date", None)
        mock_avatar.assert_called_with("dummy_user", ssl_verify=True)
        mock_pagure_review.assert_called_with(
            user="dummy_user",
            title="dummy_title",
            url="https://pagure.io/mock_repo_reference/pull-request/mock_id",
            time="mock_strptime_date",
            updated_time="mock_strptime_date",
            comments=3,
            image="dummy_avatar",
            last_comment="dummy_last_comment",
            project_name="mock_repo_reference",
            project_url="https://pagure.io/mock_repo_reference",
        )
        self.assertEqual(response, ["1"])

    @patch(PATH + "PagureService._call_api")
    @patch(PATH + "PagureService.get_last_comment")
    @patch(PATH + "datetime")
    @patch(PATH + "PagureService.check_request_state")
    @patch(PATH + "PagureService.has_new_comments")
    @patch(PATH + "PagureReview")
    @patch(PATH + "PagureService._avatar")
    def test_request_reviews_no_repo(
        self,
        mock_avatar,
        mock_pagure_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_datetime,
        mock_get_last_comment,
        mock_call_api,
    ):
        """
        Tests 'request_reviews' function without repos.

        and:
            * no last comment,
            * check_request_state returns True
            * _call_api raises a HTTPError,
            * no namespace
        """
        # Set up mock return values and side effects
        mock_call_api.side_effect = requests.exceptions.HTTPError

        # Call function
        with self.assertRaises(Exception):
            PagureService().request_reviews(user_name="dummy_user")

        # Validate function calls and response
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/dummy_user/pull-requests", ssl_verify=True
        )
        mock_get_last_comment.assert_not_called()
        mock_datetime.strptime.assert_not_called()
        mock_has_new_comments.assert_not_called()
        mock_check_request_state.assert_not_called()
        mock_avatar.assert_not_called()
        mock_pagure_review.assert_not_called()

    @patch(PATH + "PagureService._call_api")
    @patch(PATH + "PagureService.get_last_comment")
    @patch(PATH + "datetime")
    @patch(PATH + "PagureService.check_request_state")
    @patch(PATH + "PagureService.has_new_comments")
    @patch(PATH + "PagureReview")
    @patch(PATH + "PagureService._avatar")
    def test_request_reviews_with_repo_last_comment(
        self,
        mock_avatar,
        mock_pagure_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_datetime,
        mock_get_last_comment,
        mock_call_api,
    ):
        """
        Tests 'request_reviews' function with repos.

        and:
            * with last comment,
            * check_request_state returns True
            * no errors,
            * no namespace
        """
        # Set up mock return values and side effects
        mock_check_request_state.return_value = True
        mock_avatar.return_value = "dummy_avatar"
        self.mock_last_comment.created_at = "dummy_date"
        mock_get_last_comment.return_value = self.mock_last_comment
        mock_datetime.utcfromtimestamp.return_value = self.mock_utcfromtimestamp
        mock_datetime.strptime.return_value = "mock_strptime_date"
        mock_pagure_review.return_value = "1"
        mock_call_api.return_value = mock_pagure.mock_api_call_return_value()

        # Call function
        response = PagureService().request_reviews(
            user_name="dummy_user", repo_name="dummy_repo", show_last_comment=True
        )

        # Validate function calls and response
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/dummy_user/dummy_repo/pull-requests",
            ssl_verify=True,
        )
        mock_get_last_comment.assert_called_with(
            mock_call_api.return_value["requests"][0]
        )
        mock_datetime.strptime.assert_called_with("mock_date", "%Y-%m-%d %H:%M:%S.%f")
        mock_has_new_comments.assert_called_with("dummy_date", True)
        mock_check_request_state.assert_called_with("mock_strptime_date", None)
        mock_avatar.assert_not_called()
        mock_pagure_review.assert_not_called()
        self.assertEqual(response, [])

    @patch(PATH + "PagureService._call_api")
    @patch(PATH + "PagureService.get_last_comment")
    @patch(PATH + "datetime")
    @patch(PATH + "PagureService.check_request_state")
    @patch(PATH + "PagureService.has_new_comments")
    @patch(PATH + "PagureReview")
    @patch(PATH + "PagureService._avatar")
    def test_request_reviews_with_repo_with_age(
        self,
        mock_avatar,
        mock_pagure_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_datetime,
        mock_get_last_comment,
        mock_call_api,
    ):
        """
        Tests 'request_reviews' function with repos.

        and:
            * no last comment,
            * check_request_state returns False
            * no errors,
            * no namespace
        """
        # Set up mock return values and side effects
        mock_check_request_state.return_value = False
        mock_get_last_comment.return_value = "dummy_last_comment"
        mock_datetime.utcfromtimestamp.return_value = self.mock_utcfromtimestamp_error
        mock_datetime.strptime.side_effect = [ValueError, "mock_date", "mock_date"]
        mock_pagure_review.return_value = "1"
        mock_call_api.return_value = mock_pagure.mock_api_call_return_value_age()

        # Call function
        response = PagureService().request_reviews(
            user_name="dummy_user", repo_name="dummy_repo", age=self.mock_age
        )

        # Validate function calls and response
        mock_call_api.assert_called_with(
            url="https://pagure.io/api/0/dummy_user/dummy_repo/pull-requests",
            ssl_verify=True,
        )
        mock_get_last_comment.assert_called_with(
            mock_call_api.return_value["requests"][0]
        )
        mock_datetime.strptime.assert_any_call(
            "2019-01-05 12:12:12", "%Y-%m-%d %H:%M:%S"
        )
        mock_has_new_comments.assert_not_called()
        mock_check_request_state.assert_called_with("mock_date", self.mock_age)
        mock_avatar.assert_not_called()
        mock_pagure_review.assert_not_called()
        self.assertEqual(response, [])
