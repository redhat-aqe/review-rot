from os.path import join, dirname
import yaml
import github
import gitlab
from github.GithubException import UnknownObjectException
from gitlab.exceptions import GitlabGetError
from collections import namedtuple
import datetime
from reviewrot.basereview import LastComment
from reviewrot.phabricatorstack import PhabricatorReview


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
    age=None,
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
    age=None,
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


# Phabricator

def mock_phabricator_differential_query(status, responsibleUsers, phab):
    class MockResponse:
        def __init__(self, json_data, status):
            self.json_data = json_data
            self.status = status

        def json(self):
            return self.json_data

        def next(self):
            return

        def getresponse(self):
            return self.json_data

    res = [
        {
            'reviewers': [
                'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
                'PHID-USER-xxxxxxxxxxxxxxxxxxxx'
            ],
            'lineCount': '2',
            'repositoryPHID': None,
            'id': 1706,
            'authorPHID': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
            'title': 'Title 1',
            'activeDiffPHID': 'PHID-DIFF-xxxxxxxxxxxxxxxxxxxx',
            'branch': 'new_input_data',
            'dateModified': '1553524722',
            'status': '2',
            'testPlan': '',
            'commits': [],
            'dateCreated': '1553065630',
            'hashes': [],
            'properties': [],
            'diffs': [
                '3605',
                '3599'
            ],
            'phid': 'PHID-DREV-xxxxxxxxxxxxxxxxxxxx',
            'uri': 'dummy.url',
            'css': [],
            'summary': 'This is a summary.',
            'statusName': 'Accepted'
        },
    ]
    return res


def mock_phabricator_get_comments(id, phab):
    return [
                {
                    'action': 'comment',
                    'authorPHID': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
                    'revisionID': id,
                    'content': 'This is some content',
                    'dateCreated': '1551763640'
                }
        ]

def mock_phabricator_get_comments_(id, phab):
    return [
                {
                    'action': 'comment',
                    'authorPHID': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
                    'revisionID': id,
                    'content': 'This is some content',
                    'dateCreated': '1551763640'
                },
                {
                    'action': 'comment',
                    'authorPHID': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
                    'revisionID': id,
                    'content': 'This is some content',
                    'dateCreated': '1551763640'
                },
                {
                    'action': 'comment',
                    'authorPHID': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
                    'revisionID': id,
                    'content': 'This is some content',
                    'dateCreated': '1551763640'
                }
        ]


def mock_phabricator_get_reviews(phab, reviews, host, age, show_last_comment,
                                 raw_response):
    res = []
    date_created = datetime.datetime.strptime('16Sep2012', '%d%b%Y')
    date_modified = datetime.datetime.strptime('16Sep2012', '%d%b%Y')
    last_comment = LastComment(author='user_name',
                               body='content',
                               created_at=date_modified)
    temp = PhabricatorReview(user='user_name',
                             title='Title 1',
                             url='dummy.url',
                             time=date_created,
                             updated_time=date_modified,
                             comments=2,
                             image='https://authorImage.com',
                             last_comment=last_comment,
                             project_name='Phabricator',
                             project_url='www.google.com')
    res.append(temp)
    return res


def mock_phabricator_get_last_comment(comments, phab, raw_response):
    createdAt = datetime.datetime.strptime('16Sep2018', '%d%b%Y')
    return LastComment(author='user_name',
                       body='This is some content',
                       created_at=createdAt)


def mock_phabricator_user_query_ids(phids, phab):
    return [
        {
            'userName': 'dummy_user',
            'phid': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
            'realName': 'Dummy User',
            'roles': [
                'verified', 'approved', 'activated'
            ],
            'image': 'userimage.com',
            'uri': 'userurl.com'
        }
    ]

def mock_phabricator_author_data(author_phid, raw_response, phab):
    user = {
            'userName': 'dummy_user',
            'phid': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
            'realName': 'Dummy User',
            'roles': [
                'verified', 'approved', 'activated'
            ],
            'image': 'userimage.com',
            'uri': 'userurl.com'
    }

    raw_response = [
        {
            'userName': 'dummy_user',
            'phid': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
            'realName': 'Dummy User',
            'roles': [
                'verified', 'approved', 'activated'
            ],
            'image': 'userimage.com',
            'uri': 'userurl.com'
        }
    ]
    return user, raw_response


def mock_phabricator_user_serach(username, phab):
    return {
               'cursor': {
                   'after': None,
                   'limit': 100,
                   'order': None,
                   'before': None
               },
               'maps': {},
               'data': [
                   {
                       'fields': {
                            'username': 'dummyuser',
                            'realName': 'Dummy User',
                            'roles': [
                                'verified',
                                'approved',
                                'activated'],
                            'dateCreated': 1509530187,
                            'policy': {
                                'edit': 'no-one',
                                'view': 'public'},
                            'dateModified': 1509530333},
                       'phid': 'PHID-USER-xxxxxxxxxxxxxxxxxxxx',
                       'type': 'USER',
                       'id': 86,
                       'attachments': {}}],
               'query': {
                   'queryKey': None
               }
           }

def mock_phabricator_raw_response():
    return [
        {
            'userName': 'user1',
            'phid': 'PHID-USER-xxxxxxxxxxxxxxxxxx',
            'realName': 'user 1',
            'roles': [
                'verified',
                'approved',
                'activated'
            ],
            'image': 'user1.image',
            'uri': 'user1.url'
        },
        {
            'userName': 'user2',
            'phid': 'PHID-USER-xxxxxxxxxxxxxxxxxx',
            'realName': 'user 2',
            'roles': [
                'verified',
                'approved',
                'activated'
            ],
            'image': 'user2.image',
            'uri': 'user2.url'
        },
        {
            'userName': 'user3',
            'phid': 'PHID-USER-test',
            'realName': 'user 3',
            'roles': [
                'verified',
                'approved',
                'activated'
            ],
            'image': 'user3.image',
            'uri': 'user3.url'
        }
    ]

def mock_phabricator_update_interfaces():
    return

def mock_phabricator_time_from_epoch(epoch_time):
    return datetime.datetime.strptime('16Sep2012', '%d%b%Y')


class FakeReview:
    """
    Mocks small part of BaseReview
    """

    def __init__(self, title):
        self.title = title
