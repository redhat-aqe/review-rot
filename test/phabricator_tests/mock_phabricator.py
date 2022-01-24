"""This file mocks a lot of the Phabricator API calls."""


def get_comments_single():
    """Function to mock querying comments and getting a single comment back."""
    return [
        {
            "action": "comment",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "revisionID": "1",
            "content": "This is some content",
            "dateCreated": "1551763640",
        }
    ]


def get_comments_many():
    """Function to mock querying comments and getting multiple comments back."""
    return [
        {
            "action": "comment",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxx3",
            "revisionID": "1",
            "content": "This is some content",
            "dateCreated": "1551763640",
        },
        {
            "action": "comment",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "revisionID": "1",
            "content": "This is some content",
            "dateCreated": "1551763640",
        },
        {
            "action": "comment",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "revisionID": "1",
            "content": "This is some content",
            "dateCreated": "1551763640",
        },
    ]


def get_revision_comments():
    """Function to mock 'phab.query.getrevisioncomments'."""
    return [
        [
            {
                "action": "comment",
                "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxx3",
                "revisionID": "1",
                "content": "This is some content",
                "dateCreated": "1551763640",
            },
            {
                "action": "action",
                "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
                "revisionID": "1",
                "content": "This is some content",
                "dateCreated": "1551763640",
            },
            {
                "action": "comment",
                "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
                "revisionID": "1",
                "content": "This is some more content",
                "dateCreated": "1551763640",
            },
        ]
    ]


def get_comments_return_value():
    """Function to mock the return value for test 'test_get_comments_successful'."""
    return [
        {
            "action": "comment",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxx3",
            "revisionID": "1",
            "content": "This is some content",
            "dateCreated": "1551763640",
        },
        {
            "action": "comment",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "revisionID": "1",
            "content": "This is some more content",
            "dateCreated": "1551763640",
        },
    ]


def get_reviews():
    """Function to mock getting fake reviews."""
    return [
        {
            "dateCreated": "mock_date",
            "dateModified": "mock_date",
            "id": 0,
            "title": "mock_title",
            "authorPHID": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "uri": "mock.com",
        }
    ]


def user_query_usernames():
    """Function to mock return value of querying by username."""
    return [
        {
            "userName": "dummy_user1",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxx1",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
        {
            "userName": "dummy_user2",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxx2",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
    ]


def generate_phids_response():
    """Function to mock expected value for test 'test_generate_phids_successful'."""
    raw_response = [
        {
            "userName": "dummy_user1",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxx1",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
        {
            "userName": "dummy_user2",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxx2",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
    ]
    list_of_phids = ["PHID-USER-xxxxxxxxxxxxxxxxxxx1", "PHID-USER-xxxxxxxxxxxxxxxxxxx2"]
    return list_of_phids, raw_response


def author_data_raw_response():
    """
    Function to mock expected value for tests.

        * 'test_author_data_in_rawReponse'
        * 'test_author_data_not_in_rawResponse'
        * 'test_author_data_failure'
    """
    user = {
        "userName": "dummy_user-3",
        "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxx3",
        "realName": "Dummy User",
        "roles": ["verified", "approved", "activated"],
        "image": "userimage.com",
        "uri": "userurl.com",
    }

    raw_response = [
        {
            "userName": "dummy_user",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
        {
            "userName": "dummy_user",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxxx",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
        {
            "userName": "dummy_user-3",
            "phid": "PHID-USER-xxxxxxxxxxxxxxxxxxx3",
            "realName": "Dummy User",
            "roles": ["verified", "approved", "activated"],
            "image": "userimage.com",
            "uri": "userurl.com",
        },
    ]
    return user, raw_response
