import datetime
from unittest import TestCase
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


from reviewrot.phabricatorstack import PhabricatorService
from . import mock_phabricator

PATH = 'reviewrot.phabricatorstack.'


class InternetError(Exception):
    """
    This class represents the Internet Exception mock (i.e. 404 etc.)
    """


class PhabricatorTest(TestCase):
    """
    This class represents the Phabricator test cases
    """

    def setUp(self):
        """
        Set up the testing environment.
        """
        self.mock = mock_phabricator
        self.fake_phab = MagicMock()
        self.fake_phab.differential.query.return_value = "Successful call!"
        self.fake_phab.user.query.return_value = "Successful call!"
        self.fake_phab.user.query.return_value = "Successful call!"
        self.mock_age = MagicMock()

    def test_time_from_epoch(self):
        """
        Tests 'time_from_epoch' function
        """
        # Set up mock return values and side effects
        expected_response = datetime.datetime.fromtimestamp(float(123456789))

        # Call function
        response = PhabricatorService().time_from_epoch(123456789)

        # Validate function calls and response
        self.assertEqual(response, expected_response)

    def test_differential_query_successful(self):
        """
        Tests differential_query API Call (successful)
        """
        # Set up mock return values and side effects
        expected_response = "Successful call!"
        fake_status = "Open"
        fake_responsibleUsers = ["PHID-1", "PHID-2"]

        # Call function
        response = PhabricatorService().differential_query(
            status=fake_status,
            responsibleUsers=fake_responsibleUsers,
            phab=self.fake_phab
        )

        # Validate function calls and response
        self.fake_phab.differential.query.assert_called_with(
            status=fake_status,
            responsibleUsers=fake_responsibleUsers
        )
        self.assertEqual(expected_response, response)

    def test_user_query_ids_successful(self):
        """
        Tests user_query_ids API Call (successful)
        """
        # Set up mock return values and side effects
        expected_response = "Successful call!"
        fake_PHIDS = ["PHID-1", "PHID-2"]

        # Call function
        response = PhabricatorService().user_query_ids(
            phids=fake_PHIDS,
            phab=self.fake_phab
        )

        # Validate function calls and response
        self.fake_phab.user.query.assert_called_with(
            phids=fake_PHIDS
        )
        self.assertEqual(expected_response, response)

    def test_user_query_usernames_successful(self):
        """
        Tests user_query_ids API Call (successful)
        """
        # Set up mock return values and side effects
        expected_response = "Successful call!"
        fake_usernames = ["dummy_user_1", "dummy_user_2"]

        # Call function
        response = PhabricatorService().user_query_usernames(
            usernames=fake_usernames,
            phab=self.fake_phab
        )

        # Validate function calls and response
        self.fake_phab.user.query.assert_called_with(
            usernames=fake_usernames
        )
        self.assertEqual(expected_response, response)

    @patch(PATH + 'PhabricatorService.user_query_ids')
    def test_author_data_in_rawReponse(self, mock_user_query_ids):
        """
        Tests author_data function where author_phid IS IN the raw response
        """
        # Set up mock return values and side effects
        fake_user, fake_raw_response = self.mock.author_data_rawResponse()

        # Call function
        user, raw_response = PhabricatorService().author_data(
            author_phid=fake_user['phid'],
            raw_response=fake_raw_response,
            phab=None
        )

        # Validate function calls and response
        mock_user_query_ids.assert_not_called()
        self.assertEqual(fake_user, user)
        self.assertEqual(fake_raw_response, raw_response)

    @patch(PATH + 'PhabricatorService.user_query_ids',
           return_value=["New User!"])
    def test_author_data_not_in_rawResponse(self, mock_user_query_ids):
        """
        Tests author_data function where author_phid IS NOT IN the raw response
        """
        # Set up mock return values and side effects
        expected_raw_response = ["New User!"]
        expected_user = "New User!"
        fake_user, _ = self.mock.author_data_rawResponse()

        # Call function
        user, raw_response = PhabricatorService().author_data(
            author_phid=fake_user['phid'],
            raw_response=[],
            phab=None
        )

        # Validate function calls and response
        mock_user_query_ids.assert_called_with(
            [fake_user['phid']],
            None
        )
        self.assertEqual(expected_user, user)
        self.assertEqual(expected_raw_response, raw_response)

    @patch(PATH + 'PhabricatorService.user_query_ids',
           side_effect=InternetError)
    def test_author_data_failure(self, mock_user_query_ids):
        """
        Tests author_data function where user_query_ids throws an error (phab APIError)
        """
        # Set up mock return values and side effects
        fake_user, _ = self.mock.author_data_rawResponse()

        # Call function
        with self.assertRaises(InternetError):
            PhabricatorService().author_data(
                author_phid=fake_user['phid'],
                raw_response=[],
                phab=None
            )

        # Validate function calls and response
        mock_user_query_ids.assert_called_with(
            [fake_user['phid']],
            None
        )

    @patch(PATH + 'PhabricatorService.author_data',
           return_value=({'userName': 'dummy-user'}, []))
    @patch(PATH + 'PhabricatorService.time_from_epoch',
           return_value='dummy-time')
    @patch(PATH + 'LastComment')
    def test_get_last_comment_successful_single(self, mock_last_comment,
                                                mock_time_from_epoch,
                                                mock_author_data):
        """
        Tests get_last_comment function (successful, fake_comments have one comment)
        """
        # Set up mock return values and side effects
        mock_last_comment.return_value = MagicMock()
        fake_comments = self.mock.get_comments_single()

        # Call function
        response = PhabricatorService().get_last_comment(
            comments=fake_comments,
            phab=None,
            raw_response=[]
        )

        # Validate function calls and response
        mock_author_data.assert_called_with(
            author_phid='PHID-USER-xxxxxxxxxxxxxxxxxxxx',
            phab=None,
            raw_response=[]
        )
        mock_time_from_epoch.assert_called_with('1551763640')
        mock_last_comment.assert_called_with(
            author='dummy-user',
            body='This is some content',
            created_at='dummy-time'
        )
        self.assertEqual(response, mock_last_comment.return_value)

    @patch(PATH + 'PhabricatorService.author_data',
           return_value=({'userName': 'dummy-user'}, []))
    @patch(PATH + 'PhabricatorService.time_from_epoch',
           return_value='dummy-time')
    @patch(PATH + 'LastComment')
    def test_get_last_comment_successful_multiple(self, mock_last_comment,
                                                  mock_time_from_epoch,
                                                  mock_author_data):
        """
        Tests get_last_comment function (successful, fake_comments have 3 comments)
        """
        # Set up mock return values and side effects
        mock_last_comment.return_value = MagicMock()
        fake_comments = self.mock.get_comments_many()

        # Call function
        response = PhabricatorService().get_last_comment(
            comments=fake_comments,
            phab=None,
            raw_response=[]
        )

        # Validate function calls and response
        mock_author_data.assert_called_with(
            author_phid='PHID-USER-xxxxxxxxxxxxxxxxxxx3',
            phab=None,
            raw_response=[]
        )
        mock_time_from_epoch.assert_called_with('1551763640')
        self.assertEqual(response, mock_last_comment.return_value)

    @patch(PATH + 'PhabricatorService.author_data',
           side_effect=InternetError)
    @patch(PATH + 'PhabricatorService.time_from_epoch',
           return_value='dummy-time')
    def test_get_last_comment_failure(self, mock_time_from_epoch,
                                      mock_author_data):
        """
        Tests get_last_comment function (failure, author_data throws exception)
        """
        # Set up mock return values and side effects
        fake_comments = self.mock.get_comments_many()

        # Call function
        with self.assertRaises(InternetError):
            PhabricatorService().get_last_comment(
                comments=fake_comments,
                phab=None,
                raw_response=[]
            )

        # Validate function calls and response
        mock_author_data.assert_called_with(
            author_phid='PHID-USER-xxxxxxxxxxxxxxxxxxx3',
            phab=None,
            raw_response=[]
        )
        mock_time_from_epoch.assert_not_called()

    def test_get_comments_successful(self):
        """
        Tests get_comments function (successful, phab does not fail)
        """
        # Set up mock return values and side effects
        expected_response = self.mock.get_comments_return_value()
        self.fake_phab.differential.getrevisioncomments.return_value = \
            self.mock.get_revision_comments()

        # Call function
        response = PhabricatorService().get_comments(
            id=0,
            phab=self.fake_phab
        )

        # Validate function calls and response
        self.fake_phab.differential.getrevisioncomments.assert_called_with(
            ids=[0]
        )
        self.assertEqual(expected_response, response)

    def test_get_comments_failure(self):
        """
        Tests get_comments function (failure, phab fails)
        """
        # Set up mock return values and side effects
        self.fake_phab.differential.getrevisioncomments.side_effect = \
            InternetError

        # Call function
        with self.assertRaises(InternetError):
            PhabricatorService().get_comments(
                id=0,
                phab=self.fake_phab
            )

        # Validate function calls and response
        self.fake_phab.differential.getrevisioncomments.assert_called_with(
            ids=[0]
        )

    @patch(PATH + 'PhabricatorService.user_query_usernames')
    def test_generate_phids_successful(self, mock_user_query_usernames):
        """
        Tests generate_phids function (successful, user_query_usernames does not fail)
        """
        # Set up mock return values and side effects
        expected_list_of_phids, expected_raw_response = \
            self.mock.generate_phids_response()
        mock_user_query_usernames.return_value = self.mock.user_query_usernames()

        # Call function
        list_of_phids, raw_response = PhabricatorService().generate_phids(
            "user_names",
            None)

        # Validate function calls and response
        self.assertEqual(expected_list_of_phids, list_of_phids)
        self.assertEqual(expected_raw_response, raw_response)
        mock_user_query_usernames.assert_called_with(
            "user_names",
            None
        )

    @patch(PATH + 'PhabricatorService.user_query_usernames',
           side_effect=InternetError)
    def test_generate_phids_failure(self, mock_user_query_usernames):
        """
        Tests generate_phids function (successful, user_query_usernames does fail)
        """
        # Call function
        with self.assertRaises(InternetError):
            list_of_phids, raw_response = PhabricatorService().generate_phids(
                "user_names",
                None)

        # Validate function calls and response
        mock_user_query_usernames.assert_called_with(
            "user_names",
            None
        )

    @patch(PATH + 'PhabricatorService.get_comments')
    @patch(PATH + 'PhabricatorService.get_last_comment')
    @patch(PATH + 'PhabricatorService.time_from_epoch')
    @patch(PATH + 'PhabricatorService.check_request_state')
    @patch(PATH + 'PhabricatorService.has_new_comments')
    @patch(PATH + 'PhabricatorService.author_data')
    @patch(PATH + 'PhabricatorReview')
    def test_get_reviews_successful_no_last_comment(self, mock_PhabricatorReview,
                                                    mock_author_data,
                                                    mock_has_new_comments,
                                                    mock_check_request_state,
                                                    mock_time_from_epoch,
                                                    mock_get_last_comment,
                                                    mock_get_comments):
        """
        Tests get_reviews function with simple parameters
        (i.e. no show_last_comment, duration, value etc.)
        """
        # Set up mock return values and side effects
        mock_PhabricatorReview.return_value = MagicMock()
        mock_time_from_epoch.return_value = "mock_date"
        fake_reviews = self.mock.get_reviews()
        mock_get_comments.return_value = "test comment"
        mock_check_request_state.return_value = True
        mock_author_data.return_value = \
            ({'userName': 'mock_user', 'image': 'mock.com'}, [])

        # Call function
        response = PhabricatorService().get_reviews(
            phab=self.fake_phab,
            reviews=fake_reviews,
            raw_response=[],
            host="www.google.com",
            age=self.mock_age)

        # Validate function calls and response
        mock_get_comments.assert_called_with(id=0, phab=self.fake_phab)
        mock_get_last_comment(
            comments=mock_get_comments.return_value,
            phab=self.fake_phab,
            raw_response=[])
        mock_time_from_epoch.assert_called_with('mock_date')
        mock_check_request_state.assert_called_with('mock_date', self.mock_age)
        mock_has_new_comments.assert_not_called()
        mock_author_data.assert_called_with(
            'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
            [],
            self.fake_phab)
        self.assertEqual(response, [mock_PhabricatorReview.return_value])

    @patch(PATH + 'PhabricatorService.get_comments')
    @patch(PATH + 'PhabricatorService.get_last_comment')
    @patch(PATH + 'PhabricatorService.time_from_epoch')
    @patch(PATH + 'PhabricatorService.check_request_state')
    @patch(PATH + 'PhabricatorService.has_new_comments')
    @patch(PATH + 'PhabricatorService.author_data')
    @patch(PATH + 'PhabricatorReview')
    def test_get_reviews_successful_with_last_comment(self, mock_PhabricatorReview,
                                                      mock_author_data,
                                                      mock_has_new_comments,
                                                      mock_check_request_state,
                                                      mock_time_from_epoch,
                                                      mock_get_last_comment,
                                                      mock_get_comments):
        """
        Tests get_reviews function with show_last_comment
        (where has_new_comment returns something)
        """
        # Set up mock return values and side effects
        mock_PhabricatorReview.return_value = MagicMock()
        mock_last_comment_object = MagicMock()
        mock_last_comment_object.created_at = "mock_created_at"
        mock_get_last_comment.return_value = mock_last_comment_object
        mock_time_from_epoch.return_value = "mock_date"
        fake_reviews = self.mock.get_reviews()
        mock_get_comments.return_value = "test comment"
        mock_check_request_state.return_value = True
        mock_author_data.return_value = \
            ({'userName': 'mock_user', 'image': 'mock.com'}, [])

        # Call function
        response = PhabricatorService().get_reviews(
            phab=self.fake_phab,
            reviews=fake_reviews,
            raw_response=[],
            host="www.google.com",
            show_last_comment=True,
            age=self.mock_age)

        # Validate function calls and response
        mock_get_comments.assert_called_with(id=0, phab=self.fake_phab)
        mock_get_last_comment.assert_called_with(
            comments=mock_get_comments.return_value,
            phab=self.fake_phab,
            raw_response=[])
        mock_time_from_epoch.assert_called_with('mock_date')
        mock_check_request_state.assert_called_with('mock_date',
                                                    self.mock_age)
        mock_has_new_comments.assert_called_with(
            "mock_created_at", True
        )
        mock_author_data.assert_not_called()
        self.assertEqual(response, [])

    @patch(PATH + 'PhabricatorService.get_comments')
    @patch(PATH + 'PhabricatorService.get_last_comment')
    @patch(PATH + 'PhabricatorService.time_from_epoch')
    @patch(PATH + 'PhabricatorService.check_request_state')
    @patch(PATH + 'PhabricatorService.has_new_comments')
    @patch(PATH + 'PhabricatorService.author_data')
    @patch(PATH + 'PhabricatorReview')
    def test_get_reviews_successful_request_state(self, mock_PhabricatorReview,
                                                  mock_author_data,
                                                  mock_has_new_comments,
                                                  mock_check_request_state,
                                                  mock_time_from_epoch,
                                                  mock_get_last_comment,
                                                  mock_get_comments):
        """
        Tests get_reviews function with check_request_state returning false
        """
        # Set up mock return values and side effects
        mock_PhabricatorReview.return_value = MagicMock()
        mock_last_comment_object = MagicMock()
        mock_last_comment_object.created_at = "mock_created_at"
        mock_get_last_comment.return_value = mock_last_comment_object
        mock_time_from_epoch.return_value = "mock_date"
        fake_reviews = self.mock.get_reviews()
        mock_get_comments.return_value = "test comment"
        mock_check_request_state.return_value = False
        mock_author_data.return_value = \
            ({'userName': 'mock_user', 'image': 'mock.com'}, [])

        # Call function
        response = PhabricatorService().get_reviews(
            phab=self.fake_phab,
            reviews=fake_reviews,
            raw_response=[],
            host="www.google.com",
            show_last_comment=True,
            age=self.mock_age)

        # Validate function calls and response
        mock_get_comments.assert_called_with(id=0, phab=self.fake_phab)
        mock_get_last_comment(
            comments=mock_get_comments.return_value,
            phab=self.fake_phab,
            raw_response=[])
        mock_time_from_epoch.assert_called_with('mock_date')
        mock_check_request_state.assert_called_with('mock_date', self.mock_age)
        mock_has_new_comments.assert_not_called()
        mock_author_data.assert_not_called()
        self.assertEqual(response, [])

    @patch(PATH + 'Phabricator')
    @patch(PATH + 'PhabricatorService.generate_phids')
    @patch(PATH + 'PhabricatorService.differential_query')
    @patch(PATH + 'PhabricatorService.get_reviews')
    def test_request_reviews_user_names(self, mock_get_reviews,
                                        mock_differential_query,
                                        mock_generate_phids,
                                        mock_Phabricator):
        """
        Tests request_reviews with user names specified
        """
        # Set up mock return values and side effects
        mock_generate_phids.return_value = ([], 'PHID-USER-xxxxxxxxxxxxxxxxxxxx')
        mock_differential_query.return_value = 'mock_reviews'
        mock_Phabricator.return_value = self.fake_phab
        mock_get_reviews.return_value = '1'

        # Call function
        response = PhabricatorService().request_reviews(
            host="https://www.dummy.com",
            token="dummy_token",
            user_names='test_user')

        # Validate function calls and response
        mock_generate_phids.assert_called_with(
            'test_user', self.fake_phab
        )
        mock_differential_query.assert_called_with(
            status='status-open',
            responsibleUsers=[],
            phab=self.fake_phab
        )
        mock_Phabricator.assert_called_with(
            host="https://www.dummy.com/api/",
            token="dummy_token"
        )
        self.assertEqual(['1'], response)

    @patch(PATH + 'Phabricator')
    @patch(PATH + 'PhabricatorService.generate_phids')
    @patch(PATH + 'PhabricatorService.differential_query')
    @patch(PATH + 'PhabricatorService.get_reviews')
    def test_request_reviews_no_user_names(self, mock_get_reviews,
                                           mock_differential_query,
                                           mock_generate_phids,
                                           mock_Phabricator):
        """
        Tests request_reviews without user names specified
        """
        # Set up mock return values and side effects
        mock_generate_phids.return_value = ([], 'PHID-USER-xxxxxxxxxxxxxxxxxxxx')
        mock_differential_query.return_value = 'mock_reviews'
        mock_Phabricator.return_value = self.fake_phab
        mock_get_reviews.return_value = '1'

        # Call function
        response = PhabricatorService().request_reviews(
            host="https://www.dummy.com",
            token="dummy_token",
            user_names=None)

        # Validate function calls and response
        mock_generate_phids.assert_not_called()
        mock_differential_query.assert_called_with(
            status='status-open',
            responsibleUsers=[],
            phab=self.fake_phab
        )
        mock_Phabricator.assert_called_with(
            host="https://www.dummy.com/api/",
            token="dummy_token"
        )
        self.assertEqual(['1'], response)

    @patch(PATH + 'Phabricator')
    @patch(PATH + 'PhabricatorService.generate_phids')
    @patch(PATH + 'PhabricatorService.differential_query')
    @patch(PATH + 'PhabricatorService.get_reviews')
    def test_request_reviews_no_response(self, mock_get_reviews,
                                         mock_differential_query,
                                         mock_generate_phids,
                                         mock_Phabricator):
        """
        Tests request_reviews where get_reviews returns nothing
        """
        # Set up mock return values and side effects
        mock_generate_phids.return_value = ([], 'PHID-USER-xxxxxxxxxxxxxxxxxxxx')
        mock_differential_query.return_value = 'mock_reviews'
        mock_Phabricator.return_value = self.fake_phab
        mock_get_reviews.return_value = None

        # Call function
        response = PhabricatorService().request_reviews(
            host="https://www.dummy.com",
            token="dummy_token",
            user_names=None)

        # Validate function calls and response
        mock_generate_phids.assert_not_called()
        mock_differential_query.assert_called_with(
            status='status-open',
            responsibleUsers=[],
            phab=self.fake_phab
        )
        mock_Phabricator.assert_called_with(
            host="https://www.dummy.com/api/",
            token="dummy_token"
        )
        self.assertEqual([], response)
