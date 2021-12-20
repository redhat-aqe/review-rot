"""Github Tests Cases."""
import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from github.GithubException import UnknownObjectException
from reviewrot.githubstack import GithubService

from . import mock_github


PATH = "reviewrot.githubstack."

# Disable logging to avoid messing up test output
logging.disable(logging.CRITICAL)


class GithubTest(TestCase):
    """This class represents the Github test cases."""

    @patch(PATH + "LastComment")
    def test_get_last_comment_review_issue_comment_older(self, mock_lastcomment):
        """
        Tests get_last_comment function with review and issue comments.

        Where:
        * last_issue_comment.created at < last_review_comment.created_at
        """
        # Set up mock return values and side effects
        mock_lastcomment.return_value = "Successful call!"
        mock_pr = MagicMock()
        mock_pr.get_comments.return_value = mock_github.MockGithubComments()
        mock_pr.get_issue_comments.return_value = mock_github.MockGithubCommentsOlder()
        response = GithubService().get_last_comment(mock_pr)

        # Call function
        mock_lastcomment.assert_called_with(
            author="dummy_user", body="dummy_body", created_at=1
        )

        # Validate function calls and response
        self.assertEqual(response, mock_lastcomment.return_value)

    @patch(PATH + "LastComment")
    def test_get_last_comment_review_issue_comment_newer(self, mock_lastcomment):
        """
        Tests get_last_comment function with review and issue comments.

        Where
            * last_issue_comment.created at > last_review_comment.created_at
        """
        # Set up mock return values and side effects
        mock_lastcomment.return_value = "Successful call!"
        mock_pr = MagicMock()
        mock_pr.get_comments.return_value = mock_github.MockGithubCommentsOlder()
        mock_pr.get_issue_comments.return_value = mock_github.MockGithubComments()
        response = GithubService().get_last_comment(mock_pr)

        # Call function
        mock_lastcomment.assert_called_with(
            author="dummy_user", body="dummy_body", created_at=1
        )

        # Validate function calls and response
        self.assertEqual(response, mock_lastcomment.return_value)

    @patch(PATH + "LastComment")
    def test_get_last_comment_nothing(self, mock_lastcomment):
        """Tests get_last_comment function without reviews and issue comments."""
        # Set up mock return values and side effects
        mock_pr = MagicMock()
        mock_pr.get_comments.return_value = mock_github.MockGithubCommentsEmpty()
        mock_pr.get_issue_comments.return_value = mock_github.MockGithubCommentsEmpty()

        # Call function
        response = GithubService().get_last_comment(mock_pr)

        # Validate function calls and response
        mock_lastcomment.assert_not_called()
        self.assertIsNone(response)

    @patch(PATH + "GithubService.check_request_state")
    @patch(PATH + "GithubService.get_last_comment")
    @patch(PATH + "GithubReview")
    @patch(PATH + "GithubService.has_new_comments")
    def test_get_reviews_get_repo_fails(
        self,
        mock_has_new_comments,
        mock_githubreview,
        mock_last_comment,
        mock_check_request_state,
    ):
        """Tests get_reviews function where getting the repo fails."""
        # Set up mock return values and side effects
        mock_uname = MagicMock()
        mock_uname.get_repo.side_effect = UnknownObjectException(
            status=101,
            data=101,
            headers=None,
        )

        # Call function
        with self.assertRaises(Exception):
            GithubService().get_reviews(uname=mock_uname, repo_name="dummy_repo")

        # Validate function calls and response
        mock_uname.get_repo.assert_called_with("dummy_repo")
        mock_has_new_comments.assert_not_called()
        mock_githubreview.assert_not_called()
        mock_last_comment.assert_not_called()
        mock_check_request_state.assert_not_called()

    @patch(PATH + "GithubService.check_request_state")
    @patch(PATH + "GithubService.get_last_comment")
    @patch(PATH + "GithubReview")
    @patch(PATH + "GithubService.has_new_comments")
    def test_get_reviews_no_pulls(
        self,
        mock_has_new_comments,
        mock_githubreview,
        mock_last_comment,
        mock_check_request_state,
    ):
        """
        Tests get_reviews() function.

        Where getting the pull requests returns nothing.
        """
        # Set up mock return values and side effects
        mock_uname = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        mock_uname.get_repo.return_value = mock_repo

        # Call function
        response = GithubService().get_reviews(uname=mock_uname, repo_name="dummy_repo")

        # Validate function calls and response
        mock_uname.get_repo.assert_called_with("dummy_repo")
        self.assertEqual([], response)
        mock_has_new_comments.assert_not_called()
        mock_githubreview.assert_not_called()
        mock_last_comment.assert_not_called()
        mock_check_request_state.assert_not_called()

    @patch(PATH + "GithubService.check_request_state")
    @patch(PATH + "GithubService.get_last_comment")
    @patch(PATH + "GithubReview")
    @patch(PATH + "GithubService.has_new_comments")
    def test_get_reviews_with_pulls_no_age_no_last(
        self,
        mock_has_new_comments,
        mock_githubreview,
        mock_last_comment,
        mock_check_request_state,
    ):
        """
        Tests get_reviews() function.

        Where getting the pull requests returns content but check_request_state returns
        True and no show_last_comment.
        """
        # Set up mock return values and side effects
        mock_uname = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [mock_github.MockPull]
        mock_repo.full_name = "mock_full_name"
        mock_repo.html_url = "mock_url"
        mock_uname.get_repo.return_value = mock_repo
        mock_check_request_state.return_value = True
        mock_githubreview.return_value = "Successful call!"
        mock_last_comment.return_value = "mock_last_comment"

        # Call function
        response = GithubService().get_reviews(
            uname=mock_uname, repo_name="dummy_repo", age=None, show_last_comment=None
        )

        # Validate function calls and response
        mock_githubreview.assert_called_with(
            comments="dummy_commentsdummy_comments",
            image="dummy_url",
            last_comment="mock_last_comment",
            project_name="mock_full_name",
            project_url="mock_url",
            time="dummy_createdAt",
            title="dummy_title",
            updated_time="dummy_update",
            url="dummy_url",
            user="dummy_user",
        )
        mock_uname.get_repo.assert_called_with("dummy_repo")
        mock_check_request_state.assert_called_with(
            "dummy_createdAt",
            None,
        )
        mock_last_comment.assert_called_with(mock_github.MockPull)
        mock_has_new_comments.assert_not_called()
        self.assertEqual(["Successful call!"], response)

    @patch(PATH + "GithubService.check_request_state")
    @patch(PATH + "GithubService.get_last_comment")
    @patch(PATH + "GithubReview")
    @patch(PATH + "GithubService.has_new_comments")
    def test_get_reviews_with_pulls_with_age_no_last(
        self,
        mock_has_new_comments,
        mock_githubreview,
        mock_last_comment,
        mock_check_request_state,
    ):
        """
        Tests get_reviews function.

        Where getting the pull requests returns content but check_request_state returns
        True and no show_last_comment.
        """
        # Set up mock return values and side effects
        mock_uname = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [mock_github.MockPull]
        mock_uname.get_repo.return_value = mock_repo
        mock_age = MagicMock()
        mock_age.state = "mock_state"
        mock_check_request_state.return_value = False
        mock_githubreview.return_value = "Successful call!"

        # Call function
        response = GithubService().get_reviews(
            uname=mock_uname,
            repo_name="dummy_repo",
            age=mock_age,
            show_last_comment=None,
        )

        # Validate function calls and response
        mock_uname.get_repo.assert_called_with("dummy_repo")
        mock_check_request_state.assert_called_with(
            "dummy_createdAt",
            mock_age,
        )
        mock_last_comment.assert_called_with(mock_github.MockPull)
        mock_has_new_comments.assert_not_called()
        self.assertEqual([], response)

    @patch(PATH + "GithubService.check_request_state")
    @patch(PATH + "GithubService.get_last_comment")
    @patch(PATH + "GithubReview")
    @patch(PATH + "GithubService.has_new_comments")
    def test_get_reviews_with_pulls_no_age_with_last(
        self,
        mock_has_new_comments,
        mock_githubreview,
        mock_last_comment,
        mock_check_request_state,
    ):
        """
        Tests get_reviews() function.

        Where getting the pull requests returns content but check_request_state returns
        True and no show_last_comment.
        """
        # Set up mock return values and side effects
        mock_uname = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [mock_github.MockPull]
        mock_uname.get_repo.return_value = mock_repo
        mock_last_comment.return_value = mock_github.MockValue
        mock_check_request_state.return_value = True
        mock_githubreview.return_value = "Successful call!"

        # Call function
        response = GithubService().get_reviews(
            uname=mock_uname, repo_name="dummy_repo", age=None, show_last_comment=1
        )

        # Validate function calls and response
        mock_uname.get_repo.assert_called_with("dummy_repo")
        mock_check_request_state.assert_called_with(
            "dummy_createdAt",
            None,
        )
        mock_has_new_comments.assert_called_with(1, 1)
        mock_last_comment.assert_called_with(mock_github.MockPull)
        self.assertEqual([], response)

    @patch(PATH + "Github")
    def test_request_reviews_failed_user(self, mock_github_patch):
        """
        Tests request_reviews().

        Except the getting the Github user should throw an exception.
        """
        # Set up mock return values and side effects
        mock_github_instance = MagicMock(name="mock_github_instance")
        mock_github_instance.get_user.side_effect = UnknownObjectException(
            data="",
            status=101,
            headers=None,
        )
        mock_github_patch.return_value = mock_github_instance

        # Call function
        with self.assertRaises(Exception) as context:
            GithubService().request_reviews(user_name="dummy_user", token="dummy_token")

        # Validate function calls and response
        self.assertIn(
            "Invalid username/organizaton: dummy_user", context.exception.__str__()
        )
        mock_github_instance.get_user.assert_called_with("dummy_user")
        mock_github_patch.assert_called_with("dummy_token")

    @patch(PATH + "Github")
    @patch(PATH + "GithubService.get_reviews")
    def test_request_reviews_with_repo(self, mock_get_reviews, mock_github_patch):
        """Tests request_reviews with repos."""
        # Set up mock return values and side effects
        mock_github_instance = MagicMock()
        mock_user_object = MagicMock()
        mock_github_instance.get_user.return_value = mock_user_object
        mock_get_reviews.return_value = "1"
        mock_github_patch.return_value = mock_github_instance

        # Call function
        response = GithubService().request_reviews(
            user_name="dummy_user",
            repo_name="dummy_repo",
            token="dummy_token",
        )

        # Validate function calls and response
        mock_get_reviews.assert_called_with(
            uname=mock_user_object,
            repo_name="dummy_repo",
            age=None,
            show_last_comment=None,
        )
        mock_user_object.get_repos.assert_not_called()
        mock_github_instance.get_user.assert_called_with("dummy_user")
        mock_github_patch.assert_called_with("dummy_token")
        self.assertEqual(["1"], response)

    @patch(PATH + "Github")
    @patch(PATH + "GithubService.get_reviews")
    def test_request_reviews_without_repo(self, mock_get_reviews, mock_github_patch):
        """Tests request_reviews without repos."""
        # Set up mock return values and side effects
        mock_github_instance = MagicMock()
        mock_user_object = MagicMock()
        mock_user_object.get_repos.return_value = [mock_github.MockRepo]
        mock_github_instance.get_user.return_value = mock_user_object
        mock_get_reviews.return_value = "1"
        mock_github_patch.return_value = mock_github_instance

        # Call function
        response = GithubService().request_reviews(
            user_name="dummy_user", token="dummy_token", host=None
        )

        # Validate function calls and response
        mock_get_reviews.assert_called_with(
            uname=mock_user_object,
            repo_name="dummy_repo",
            age=None,
            show_last_comment=None,
        )

        mock_user_object.get_repos.assert_any_call()
        mock_github_instance.get_user.assert_called_with("dummy_user")
        mock_github_patch.assert_called_with("dummy_token")
        self.assertEqual(["1"], response)
