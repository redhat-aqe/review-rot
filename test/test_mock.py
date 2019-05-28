from os.path import join, dirname
import yaml
import github
import gitlab
from github.GithubException import UnknownObjectException
from gitlab.exceptions import GitlabGetError
from collections import namedtuple


with open(join(dirname(__file__), "test_githubtest.yaml"), "r") as f:
    github_config = yaml.safe_load(f)

with open(join(dirname(__file__), "test_gitlabtest.yaml"), "r") as f:
    gitlab_config = yaml.safe_load(f)

# github


def mock_get_user(user_name):
    raise UnknownObjectException("param1", "param2")


def mock_get_user_(user_name):
    res = github.NamedUser.NamedUser(
        "param1", "param2", {"login": user_name}, "param3"
    )
    return res


def mock_get_repos():
    repo = github.Repository.Repository("param1", "param2", "param3", "param4")
    res = []
    res.append(repo)
    return res


def mock_github_get_reviews(
    uname,
    repo_name,
    state_=None,
    value=None,
    duration=None,
    show_last_comment=None,
):
    msg = [github_config["msg"]]
    return msg


def mock_get_repo(repo_name):
    raise UnknownObjectException("args", "kwargs")


def mock_get_repo_(repo_name):
    repo = github.Repository.Repository("param1", "param2", "param3", "param4")
    return repo


def mock_get_pulls():
    return []


# for mocking user in comments
User = namedtuple("User", ("login"))


class FakeGithubComment:
    """
    Mock comments in pull requests
    """

    def __init__(self, author, body, created_at):
        self.user = User(login=author)
        self.body = body
        self.created_at = created_at


class FakeGithubPaginatedList:
    """
    Mocks PaginatedList containing comments
    """

    def __init__(self, comments):
        self.comments = comments
        self.totalCount = len(comments)

    @property
    def reversed(self):
        return list(reversed(self.comments))


# gitlab


def mock_projects_get(user_name, repo_name):
    return GitlabGetError()


def mock_projects_get_():
    return gitlab.Gitlab.projects.create({"name": "project"})


def mock_auth():
    return True


def mock_groups_search(user_name):
    return []


def mock_gitlab_get_reviews(
    uname,
    project,
    state_=None,
    value=None,
    duration=None,
    show_last_comment=None,
):
    msg = [gitlab_config["msg"]]
    return msg


class FakeProjectMergeRequestNote:
    """
    Mocks discussion note in merge requests
    """

    def __init__(self, system, author, created_at, body):
        self.system = system
        self.author = {"username": author}
        self.created_at = created_at
        self.body = body
