"""Test gitlab."""
from datetime import datetime
import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from gitlab.exceptions import GitlabGetError, GitlabListError
from requests.exceptions import SSLError
from reviewrot.gitlabstack import GitlabService


PATH = "reviewrot.gitlabstack."

# Disable logging to avoid messing up test output
logging.disable(logging.CRITICAL)


class GitlabTest(TestCase):
    """This class represents the Gitlab test cases."""

    def setUp(self):
        """Set up the testing environment. Load mock."""
        # Mock Merge Requests
        self.mock_merge_request = MagicMock(name="mock_merge_request")
        self.mock_merge_request = MagicMock(name="mock_merge_request")
        self.mock_merge_request.system = []
        self.mock_merge_request.author = {"username": "dummy_author"}
        self.mock_merge_request.body = "dummy_body"
        self.mock_merge_request.created_at = "2010-10-04T03:41:22.858Z"

        # Mock Individual Merge Request
        self.mock_mr = MagicMock(name="mock_mr")
        self.mock_mr.created_at = "2010-10-04T03:41:22.858Z"
        self.mock_mr.updated_at = "2010-10-04T03:41:22.858Z"
        self.mock_mr.author = {"username": "dummy_user"}
        self.mock_mr.title = "dummy_title"
        self.mock_mr.web_url = "dummy_url"
        self.mock_mr.user_notes_count = 1

        # Mock Project
        self.mock_project = MagicMock(name="mock_project")
        self.mock_project.id = 1
        self.mock_project.name = "dummy_project"
        self.mock_project.web_url = "dummy_url"

        # Mock Last Comment
        self.mock_last_comment = MagicMock(name="mock_last_comment")
        self.mock_last_comment.created_at = "dummy_created_at"

    @patch(PATH + "LastComment")
    def test_get_last_comment_with_note_system(self, mock_last_comment):
        """
        Test 'get_last_comment' function.

        With all notes in mr.notes.list() not having note.system
        """
        # Set up mock return values and side effects
        mock_merge_requests = MagicMock()
        mock_merge_requests.notes.list().return_value = ["test"]

        # Call function
        response = GitlabService().get_last_comment(mock_merge_requests)

        # Validate function calls and response
        mock_last_comment.assert_not_called()
        self.assertEqual(None, response)

    @patch(PATH + "LastComment")
    def test_get_last_comment_no_note_system(self, mock_last_comment):
        """
        Test 'get_last_comment' function.

        With all notes in mr.notes.list() having note.system
        """
        # Set up mock return values and side effects
        mock_merge_requests = MagicMock(name="mock_merge_requests")
        created_at_expected_response = datetime.strptime(
            self.mock_merge_request.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        mock_last_comment.return_value = "Successful Call!"
        mock_merge_requests.notes.list.return_value = [self.mock_merge_request]

        # Call function
        response = GitlabService().get_last_comment(mock_merge_requests)

        # Validate function calls and response
        mock_last_comment.assert_called_with(
            author="dummy_author",
            body="dummy_body",
            created_at=created_at_expected_response,
        )

        self.assertEqual("Successful Call!", response)

    @patch(PATH + "GitlabService.get_last_comment")
    @patch(PATH + "GitlabService.check_request_state")
    @patch(PATH + "GitlabService.has_new_comments")
    @patch(PATH + "GitlabReview")
    def test_get_reviews_gitlab_list_error(
        self,
        mock_gitlab_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_get_last_comment,
    ):
        """Test 'get_reviews' where getting merge requests throws GitlabListError."""
        # Set up mock return values and side effects
        self.mock_project.mergerequests.list.side_effect = GitlabListError()

        # Call function
        response = GitlabService().get_reviews(
            uname="dummy_user",
            project=self.mock_project,
        )

        # Validate function calls and response
        self.mock_project.mergerequests.list.assert_called_with(
            project_id=1, state="opened"
        )
        mock_gitlab_review.assert_not_called()
        mock_has_new_comments.assert_not_called()
        mock_check_request_state.assert_not_called()
        mock_get_last_comment.assert_not_called()
        self.assertEqual(response, [])

    @patch(PATH + "GitlabService.get_last_comment")
    @patch(PATH + "GitlabService.check_request_state")
    @patch(PATH + "GitlabService.has_new_comments")
    @patch(PATH + "GitlabReview")
    def test_get_reviews_value_error(
        self,
        mock_gitlab_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_get_last_comment,
    ):
        """
        Test 'get_reviews'.

        Where we have no age and no last comment
        and datetime.strptime throws a ValueError
        """
        # Set up mock return values and side effects
        self.mock_mr.updated_at = "2010-10-04T03:41:22Z"
        self.mock_mr.created_at = "2010-10-04T03:41:22Z"
        expected_date = datetime.strptime("2010-10-04T03:41:22Z", "%Y-%m-%dT%H:%M:%SZ")
        self.mock_project.mergerequests.list.return_value = [self.mock_mr]
        mock_get_last_comment.return_value = self.mock_last_comment
        mock_check_request_state.return_value = True
        mock_gitlab_review.return_value = "Successful Call!"
        mock_gitlab_review.logo = "dummy_logo"

        # Call function
        response = GitlabService().get_reviews(
            uname="dummy_user",
            project=self.mock_project,
        )

        # Validate function calls and response
        self.mock_project.mergerequests.list.assert_called_with(
            project_id=1, state="opened"
        )
        mock_check_request_state.assert_called_with(
            expected_date,
            None,
        )
        mock_get_last_comment.assert_called_with(self.mock_mr)
        mock_gitlab_review.assert_called_with(
            user="dummy_user",
            title="dummy_title",
            url="dummy_url",
            time=expected_date,
            updated_time=expected_date,
            comments=1,
            image="dummy_logo",
            last_comment=self.mock_last_comment,
            project_name="dummy_project",
            project_url="dummy_url",
        )
        mock_has_new_comments.assert_not_called()
        self.assertEqual(response, ["Successful Call!"])

    @patch(PATH + "GitlabService.get_last_comment")
    @patch(PATH + "GitlabService.check_request_state")
    @patch(PATH + "GitlabService.has_new_comments")
    @patch(PATH + "GitlabReview")
    def test_get_reviews_no_age_no_last_comment(
        self,
        mock_gitlab_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_get_last_comment,
    ):
        """Test 'get_reviews' where we have no age and no last comment."""
        # Set up mock return values and side effects
        expected_date = datetime.strptime(
            self.mock_mr.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.mock_project.mergerequests.list.return_value = [self.mock_mr]
        mock_get_last_comment.return_value = self.mock_last_comment
        mock_check_request_state.return_value = True
        mock_gitlab_review.return_value = "Successful Call!"
        mock_gitlab_review.logo = "dummy_logo"

        # Call function
        response = GitlabService().get_reviews(
            uname="dummy_user",
            project=self.mock_project,
        )

        # Validate function calls and response
        self.mock_project.mergerequests.list.assert_called_with(
            project_id=1, state="opened"
        )
        mock_check_request_state.assert_called_with(
            expected_date,
            None,
        )
        mock_get_last_comment.assert_called_with(self.mock_mr)
        mock_gitlab_review.assert_called_with(
            user="dummy_user",
            title="dummy_title",
            url="dummy_url",
            time=expected_date,
            updated_time=expected_date,
            comments=1,
            image="dummy_logo",
            last_comment=self.mock_last_comment,
            project_name="dummy_project",
            project_url="dummy_url",
        )
        mock_has_new_comments.assert_not_called()
        self.assertEqual(response, ["Successful Call!"])

    @patch(PATH + "GitlabService.get_last_comment")
    @patch(PATH + "GitlabService.check_request_state")
    @patch(PATH + "GitlabService.has_new_comments")
    @patch(PATH + "GitlabReview")
    def test_get_reviews_with_age_no_last_comment(
        self,
        mock_gitlab_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_get_last_comment,
    ):
        """Test 'get_reviews' where we have a age and no last comment."""
        # Set up mock return values and side effects
        expected_date = datetime.strptime(
            self.mock_mr.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.mock_project.mergerequests.list.return_value = [self.mock_mr]
        mock_age = MagicMock()
        mock_age.state = "mock_state "
        mock_get_last_comment.return_value = "last_comment"
        mock_check_request_state.return_value = False
        mock_gitlab_review.logo = "dummy_logo"

        # Call function
        response = GitlabService().get_reviews(
            uname="dummy_user", project=self.mock_project, age=mock_age
        )

        # Validate function calls and response
        self.mock_project.mergerequests.list.assert_called_with(
            project_id=1, state="opened"
        )
        mock_check_request_state.assert_called_with(
            expected_date,
            mock_age,
        )
        mock_get_last_comment.assert_called_with(self.mock_mr)
        mock_gitlab_review.assert_not_called()
        mock_has_new_comments.assert_not_called()
        self.assertEqual(response, [])

    @patch(PATH + "GitlabService.get_last_comment")
    @patch(PATH + "GitlabService.check_request_state")
    @patch(PATH + "GitlabService.has_new_comments")
    @patch(PATH + "GitlabReview")
    def test_get_reviews_no_age_with_last_comment(
        self,
        mock_gitlab_review,
        mock_has_new_comments,
        mock_check_request_state,
        mock_get_last_comment,
    ):
        """Test 'get_reviews' where we have no age and with last comment."""
        # Set up mock return values and side effects
        expected_date = datetime.strptime(
            self.mock_mr.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.mock_project.mergerequests.list.return_value = [self.mock_mr]
        mock_get_last_comment.return_value = self.mock_last_comment
        mock_check_request_state.return_value = True
        mock_gitlab_review.return_value = "Successful Call!"
        mock_gitlab_review.logo = "dummy_logo"

        # Call function
        response = GitlabService().get_reviews(
            uname="dummy_user", project=self.mock_project, show_last_comment=True
        )

        # Validate function calls and response
        self.mock_project.mergerequests.list.assert_called_with(
            project_id=1, state="opened"
        )
        mock_check_request_state.assert_called_with(
            expected_date,
            None,
        )
        mock_get_last_comment.assert_called_with(self.mock_mr)
        mock_gitlab_review.assert_not_called()
        mock_has_new_comments.assert_called_with("dummy_created_at", True)
        self.assertEqual(response, [])

    @patch(PATH + "gitlab.Gitlab")
    @patch(PATH + "GitlabService.get_reviews")
    def test_request_reviews_ssl_error_no_repo(self, mock_get_reviews, mock_gitlab):
        """Test 'request_reviews' function where there is an SSL error and no repos."""
        # Set up mock return values and side effects
        mock_gitlab_project = MagicMock()
        mock_gitlab_group = MagicMock(name="mock_gitlab_group")
        mock_gitlab_group.id = 1
        mock_gitlab_group_projects = MagicMock()
        mock_gitlab_group_projects.projects.list.return_value = [mock_gitlab_group]
        mock_gitlab_instance = MagicMock(name="mock_gitlab_instance")
        mock_gitlab_instance.groups.get.return_value = mock_gitlab_group_projects
        mock_gitlab_instance.projects.get.return_value = mock_gitlab_project
        mock_gitlab_instance.auth.side_effect = SSLError
        mock_get_reviews.return_value = "1"
        mock_gitlab.return_value = mock_gitlab_instance

        # Call function
        response = GitlabService().request_reviews(
            user_name="dummy_user",
            token="dummy_token",
            host="dummy.com",
            ssl_verify=True,
        )

        # Validate function calls and response
        mock_gitlab.assert_called_with("dummy.com", "dummy_token", ssl_verify=True)
        mock_gitlab_instance.auth.assert_called_once()
        mock_gitlab_instance.groups.get.assert_called_with("dummy_user")
        mock_gitlab_instance.projects.get.assert_called_with(1)
        mock_get_reviews.assert_called_with(
            uname="dummy_user",
            project=mock_gitlab_project,
            age=None,
            image=mock_gitlab_project.avatar_url,
        )
        self.assertEqual(["1"], response)

    @patch(PATH + "gitlab.Gitlab")
    @patch(PATH + "GitlabService.get_reviews")
    def test_request_reviews_no_group_no_repo(self, mock_get_reviews, mock_gitlab):
        """Test 'request_reviews' function where gl.groups.get returns None."""
        # Set up mock return values and side effects
        mock_gitlab_instance = MagicMock(name="mock_gitlab_instance")
        mock_gitlab_instance.projects.get.return_value = "dummy_project"
        mock_gitlab_instance.groups.get.return_value = None
        mock_gitlab.return_value = mock_gitlab_instance

        # Call function
        with self.assertRaises(Exception):
            GitlabService().request_reviews(
                user_name="dummy_user",
                token="dummy_token",
                host="dummy.com",
                ssl_verify=True,
            )

        # Validate function calls and response
        mock_gitlab.assert_called_with("dummy.com", "dummy_token", ssl_verify=True)
        mock_gitlab_instance.auth.assert_called_once()
        mock_get_reviews.assert_not_called()
        mock_gitlab_instance.groups.get.assert_called_with("dummy_user")
        mock_gitlab_instance.projects.get.assert_not_called()

    @patch(PATH + "gitlab.Gitlab")
    @patch(PATH + "GitlabService.get_reviews")
    def test_request_reviews_gitlab_get_error_with_repo(
        self, mock_get_reviews, mock_gitlab
    ):
        """
        Tests 'request_reviews' function.

        Where we have repos and gl.projects.get throws an exception
        """
        # Set up mock return values and side effects
        mock_gitlab_instance = MagicMock(name="mock_gitlab_instance")
        mock_gitlab_instance.projects.get.side_effect = GitlabGetError
        mock_gitlab.return_value = mock_gitlab_instance

        # Call function
        with self.assertRaises(Exception):
            GitlabService().request_reviews(
                user_name="dummy_user",
                token="dummy_token",
                host="dummy.com",
                ssl_verify=True,
                repo_name="dummy_repo",
            )

        # Validate function calls and response
        mock_gitlab.assert_called_with("dummy.com", "dummy_token", ssl_verify=True)
        mock_gitlab_instance.groups.get.assert_not_called()
        mock_gitlab_instance.auth.assert_called_once()
        mock_gitlab_instance.projects.get.assert_called_with("dummy_user/dummy_repo")
        mock_get_reviews.assert_not_called()

    @patch(PATH + "gitlab.Gitlab")
    @patch(PATH + "GitlabService.get_reviews")
    def test_request_reviews_with_repo_success(self, mock_get_reviews, mock_gitlab):
        """Tests 'request_reviews' function where we have repos and no errors."""
        # Set up mock return values and side effects
        mock_gitlab_instance = MagicMock(name="mock_gitlab_instance")
        mock_gitlab_project = MagicMock()
        mock_gitlab_instance.projects.get.return_value = mock_gitlab_project
        mock_gitlab_instance.projects.namespace.return_value = {"id": 123}
        mock_gitlab.return_value = mock_gitlab_instance
        mock_get_reviews.return_value = "1"

        # Call function
        response = GitlabService().request_reviews(
            user_name="dummy_user",
            token="dummy_token",
            host="dummy.com",
            ssl_verify=True,
            repo_name="dummy_repo",
        )

        # Validate function calls and response
        mock_gitlab.assert_called_with("dummy.com", "dummy_token", ssl_verify=True)
        mock_gitlab_instance.groups.get.assert_not_called()
        mock_gitlab_instance.auth.assert_called_once()
        mock_gitlab_instance.projects.get.assert_called_with("dummy_user/dummy_repo")
        mock_get_reviews.assert_called_with(
            uname="dummy_user",
            project=mock_gitlab_project,
            age=None,
            show_last_comment=None,
            image=mock_gitlab_project.avatar_url,
        )
        self.assertEqual(["1"], response)
