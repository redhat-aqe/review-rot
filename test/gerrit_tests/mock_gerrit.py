"""This file mocks some return values that are used in 'test_gerrit.py'."""


def mock_decoded_response_no_email():
    """TODO: docstring goes here."""
    return [
        {
            "created": "mock_date",
            "updated": "mock_date",
            "id": "mock_id",
            "subject": "mock_subject",
            "project": "mock_project",
            "owner": {"username": "mock_username", "email": "mock_email"},
            "_number": "mock_number",
        }
    ]


def mock_decoded_response_with_email():
    """TODO: docstring goes here."""
    return [
        {
            "created": "mock_date",
            "updated": "mock_date",
            "id": "mock_id",
            "subject": "mock_subject",
            "project": "mock_project",
            "owner": {"email": "mock_email"},
            "_number": "mock_number",
        }
    ]


def mock_comments_response():
    """TODO: docstring goes here."""
    return {
        "response": [
            {
                "updated": "mock_update",
                "author": {"username": "mock_username"},
                "message": "mock_message",
            }
        ]
    }
