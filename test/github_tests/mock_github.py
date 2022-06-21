"""This mocks a lot of the Github API classes such as comments, pulls, users, etc."""


class MockGithub:
    """Mocks Github instance."""

    def __init__(self):
        """Initializer."""
        return


class MockUser:
    """Mocks Github User instance."""

    login = "dummy_user"
    avatar_url = "dummy_url"


class MockValue:
    """Mocks Last Comment value from Github."""

    created_at = 1
    user = MockUser
    body = "dummy_body"


class MockValueOlder:
    """Mocks Last Comment value from Github."""

    created_at = 0
    user = MockUser
    body = "dummy_body"


class MockGithubComments:
    """Mocks Github Comments object."""

    totalCount = int(1)
    reversed = [MockValue]


class MockGithubCommentsOlder:
    """Mocks Github Comments object."""

    totalCount = int(1)
    reversed = [MockValueOlder]


class MockGithubCommentsEmpty:
    """Mocks Github Comment object with no comments."""

    totalCount = 0
    reversed = [MockValue]


class MockPull:
    """Mocks Github Pull request."""

    created_at = "dummy_createdAt"
    user = MockUser
    title = "dummy_title"
    html_url = "dummy_url"
    updated_at = "dummy_update"
    review_comments = "dummy_comments"
    comments = "dummy_comments"


class MockRepo:
    """Mocks Github repo."""

    name = "dummy_repo"
