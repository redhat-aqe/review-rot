import logging
import mock
import yaml
import test_mock
import unittest
from os.path import join, dirname
from unittest import TestCase
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
from reviewrot import get_git_service
from github.GithubException import BadCredentialsException
from gitlab.exceptions import GitlabConnectionError

# Disable logging to avoid messing up test output
logging.disable(logging.CRITICAL)


class GithubTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), 'test_githubtest.yaml')
        with open(filename, 'r') as f:
            self.config = yaml.load(f)

    def test_object_create(self):
        self.assertTrue(isinstance((get_git_service('github')), GithubService))

    def test_request_review_token(self):
        github = GithubService()
        with self.assertRaises(BadCredentialsException) as context:
            github.request_reviews(user_name=self.config['user_name'],
                                   token=self.config['token'])
        self.assertTrue('Bad credentials' in str(context.exception))

    @mock.patch('github.Github.get_user', side_effect=test_mock.mock_get_user)
    def test_request_reviews_get_user(self, mock_get_user):
        with self.assertRaises(Exception) as context:
            GithubService().request_reviews(user_name=self.config['user_name'],
                                            token=self.config['token'])
        msg = 'Invalid username/organizaton: %s' % self.config['user_name']
        self.assertTrue(msg in str(context.exception))

    @mock.patch('github.Github.get_user', side_effect=test_mock.mock_get_user_)
    @mock.patch('reviewrot.githubstack.GithubService.get_reviews',
                side_effect=test_mock.mock_github_get_reviews)
    def test_request_reviews_with_repo(self, mock_get_user_,
                                       mock_github_get_reviews):
        res = GithubService().request_reviews(user_name=self.config['user_name'],
                                              token=self.config['token'],
                                              repo_name=self.config['repo_name'])
        self.assertEqual([self.config['msg']], res)

    @mock.patch('github.Github.get_user', side_effect=test_mock.mock_get_user_)
    @mock.patch('github.NamedUser.NamedUser.get_repos', side_effect=test_mock.mock_get_repos)
    @mock.patch('reviewrot.githubstack.GithubService.get_reviews',
                side_effect=test_mock.mock_github_get_reviews)
    def test_request_reviews_without_repo(self, mock_get_user_,
                                          mock_github_get_reviews, mock_get_repos):
        res = GithubService().request_reviews(user_name=self.config['user_name'],
                                              token=self.config['token'])
        self.assertEqual([self.config['msg']], res)

    @mock.patch('github.NamedUser.NamedUser.get_repo', side_effect=test_mock.mock_get_repo)
    def test_get_reviews_get_repo_not_found(self, mock_get_repo):
        with self.assertRaises(Exception) as context:
            uname = test_mock.mock_get_user_(self.config['user_name'])
            GithubService().get_reviews(uname=uname,
                                        repo_name=self.config['repo_name'])
        msg = 'Repository %s not found for user %s' % (self.config['repo_name'],
                                                       uname.login)
        self.assertTrue(msg in str(context.exception))

    @mock.patch('github.NamedUser.NamedUser.get_repo', side_effect=test_mock.mock_get_repo_)
    @mock.patch('github.Repository.Repository.get_pulls', side_effect=test_mock.mock_get_pulls)
    def test_get_reviews_get_repo(self, mock_get_pulls, mock_get_repo_):
        uname = test_mock.mock_get_user_(self.config['user_name'])
        res = GithubService().get_reviews(uname=uname,
                                          repo_name=self.config['repo_name'])
        self.assertEqual(res, [])


class GitlabTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), 'test_gitlabtest.yaml')
        with open(filename, 'r') as f:
            self.config = yaml.load(f)

    def test_github_object_create(self):
        self.assertTrue(isinstance((get_git_service('gitlab')), GitlabService))

    def test_request_reviews__token(self):
        github = GitlabService()
        with self.assertRaises(GitlabConnectionError)as context:
            github.request_reviews(user_name=self.config['user_name'],
                                   token=self.config['token'],
                                   host=self.config['host'])
        self.assertTrue('NewConnectionError' in str(context.exception))

    @mock.patch('gitlab.Project.get', side_effect=test_mock.mock_projects_get)
    @mock.patch('gitlab.Gitlab.auth', side_effect=test_mock.mock_auth)
    def test_request_reviews_projects_get(self, mock_projects_get, mock_auth):
        with self.assertRaises(Exception) as context:
            GitlabService().request_reviews(user_name=self.config['user_name'],
                                            repo_name=self.config['repo_name'],
                                            token=self.config['token'],
                                            host=self.config['host'])
        msg = 'Project %s not found for user %s' % (self.config['repo_name'],
                                                    self.config['user_name'])
        self.assertTrue(msg in str(context.exception))

    @mock.patch('gitlab.GroupManager.search', side_effect=test_mock.mock_groups_search)
    @mock.patch('gitlab.Gitlab.auth', side_effect=test_mock.mock_auth)
    def test_request_reviews_groups_search(self, mock_groups_search, mock_auth):
        with self.assertRaises(Exception) as context:
            GitlabService().request_reviews(user_name=self.config['user_name'],
                                            token=self.config['token'],
                                            host=self.config['host'])
        msg = 'Invalid user/group name: %s' % self.config['user_name']
        self.assertTrue(msg in str(context.exception))

    @mock.patch('gitlab.Project.get', side_effect=test_mock.mock_projects_get_)
    @mock.patch('gitlab.Gitlab.auth', side_effect=test_mock.mock_auth)
    @mock.patch('reviewrot.gitlabstack.GitlabService.get_reviews',
                side_effect=test_mock.mock_gitlab_get_reviews)
    def test_request_reviews_with_repo(self, mock_projects_get_,
                                       mock_gitlab_get_reviews, mock_auth):
        res = GitlabService().request_reviews(user_name=self.config['user_name'],
                                              repo_name=self.config['repo_name'],
                                              token=self.config['token'],
                                              host=self.config['host'])
        self.assertEqual([self.config['msg']], res)


class PagureTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), 'test_paguretest.yaml')
        with open(filename, 'r') as f:
            self.config = yaml.load(f)

    def test_pagure_object_create(self):
        self.assertTrue(isinstance((get_git_service('pagure')), PagureService))

    def test_request_review_incorrect_project_with_repo(self):
        pagure = PagureService()
        with self.assertRaises(Exception)as context:
            pagure.request_reviews(user_name=self.config['user_name'],
                                   repo_name=self.config['repo_name'])
        self.assertTrue('Project not found' in str(context.exception))


if __name__ == '__main__':
    unittest.main()
