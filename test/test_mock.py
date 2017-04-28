from os.path import join, dirname
import yaml
import github
import gitlab
from github.GithubException import UnknownObjectException
from gitlab.exceptions import GitlabGetError


with open(join(dirname(__file__), 'test_githubtest.yaml'), 'r') as f:
    github_config = yaml.load(f)

with open(join(dirname(__file__), 'test_gitlabtest.yaml'), 'r') as f:
    gitlab_config = yaml.load(f)

# github


def mock_get_user(user_name):
    raise UnknownObjectException('param1', 'param2')


def mock_get_user_(user_name):
    res = github.NamedUser.NamedUser('param1', 'param2',
                                     {'login': user_name}, 'param3')
    return res


def mock_get_repos():
    repo = github.Repository.Repository('param1', 'param2', 'param3', 'param4')
    res = []
    res.append(repo)
    return res


def mock_github_get_reviews(uname, repo_name, state_=None,
                            value=None, duration=None):
    msg = github_config['msg']
    return msg


def mock_get_repo(repo_name):
    raise UnknownObjectException('args', 'kwargs')


def mock_get_repo_(repo_name):
    repo = github.Repository.Repository('param1', 'param2',
                                        'param3', 'param4')
    return repo


def mock_get_pulls():
    return []

# gitlab


def mock_projects_get(user_name, repo_name):
    raise GitlabGetError()


def mock_projects_get_(user_name, repo_name):
    return gitlab.Project({'key': 'value'})


def mock_auth():
    return True


def mock_groups_search(user_name):
    return []


def mock_gitlab_get_reviews(uname, project, state_=None,
                            value=None, duration=None):
    msg = gitlab_config['msg']
    return msg
