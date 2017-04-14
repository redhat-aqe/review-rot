import mock
import yaml
import test_mock
import unittest
from unittest import TestCase
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
from reviewrot.gerritstack import GerritService
from github.GithubException import BadCredentialsException


class GithubTest(TestCase):
    def test_object_create(self):
        isinstance_ = isinstance(GithubService(), GithubService)
        self.assertEqual(isinstance_, True)

    def test_request_review_token(self):
        with open('test_githubtest.yaml', 'r') as f:
            config = yaml.load(f)
        github = GithubService()
        with self.assertRaises(BadCredentialsException) as context:
            github.request_reviews(user_name=config['user_name'],
                                   token=config['token'])
        self.assertTrue('Bad credentials' in str(context.exception))

    @mock.patch('github.Github.get_user', side_effect=test_mock.mock_get_user)
    def test_request_reviews_get_user(self, mock_get_user):
        with open('test_githubtest.yaml', 'r') as f:
            config = yaml.load(f)
        with self.assertRaises(Exception) as context:
            GithubService().request_reviews(user_name=config['user_name'],
                                            token=config['token'])
        msg = 'Invalid username/organizaton: %s' % config['user_name']
        self.assertTrue(msg in str(context.exception))

    @mock.patch('github.Github.get_user', side_effect=test_mock.mock_get_user_)
    @mock.patch('reviewrot.githubstack.GithubService.get_reviews',
                side_effect=test_mock.mock_get_reviews)
    def test_request_reviews_with_repo(self, mock_get_user_, mock_get_reviews):
        with open('test_githubtest.yaml', 'r') as f:
            config = yaml.load(f)
        res = GithubService().request_reviews(user_name=config['user_name'],
                                              token=config['token'],
                                              repo_name=config['repo_name'])
        msg = config['msg']
        result = []
        result.append(msg)
        self.assertTrue(result, res)

    @mock.patch('github.Github.get_user', side_effect=test_mock.mock_get_user_)
    @mock.patch('github.NamedUser.NamedUser.get_repos', side_effect=test_mock.mock_get_repos)
    @mock.patch('reviewrot.githubstack.GithubService.get_reviews',
                side_effect=test_mock.mock_get_reviews)
    def test_request_reviews_without_repo(self, mock_get_user_,
                                          mock_get_reviews, mock_get_repos):
        with open('test_githubtest.yaml', 'r') as f:
            config = yaml.load(f)
        res = GithubService().request_reviews(user_name=config['user_name'],
                                              token=config['token'])
        msg = config['msg']
        result = []
        result.append(msg)
        self.assertTrue(result, res)

    @mock.patch('github.NamedUser.NamedUser.get_repo', side_effect=test_mock.mock_get_repo)
    def test_get_reviews_get_repo_not_found(self, mock_get_repo):
        with open('test_githubtest.yaml', 'r') as f:
            config = yaml.load(f)
        with self.assertRaises(Exception) as context:
            uname = test_mock.mock_get_user_(config['user_name'])
            GithubService().get_reviews(uname=uname,
                                        repo_name=config['repo_name'])
        msg = 'Repository %s not found for user %s' % (config['repo_name'],
                                                       uname.login)
        self.assertTrue(msg in str(context.exception))

    @mock.patch('github.NamedUser.NamedUser.get_repo', side_effect=test_mock.mock_get_repo_)
    @mock.patch('github.Repository.Repository.get_pulls', side_effect=test_mock.mock_get_pulls)
    def test_get_reviews_get_repo(self, mock_get_pulls, mock_get_repo_):
        with open('test_githubtest.yaml', 'r') as f:
            config = yaml.load(f)
        uname = test_mock.mock_get_user_(config['user_name'])
        res = GithubService().get_reviews(uname=uname,
                                          repo_name=config['repo_name'])
        self.assertTrue(res == [])


class GitlabTest(TestCase):
    def test_github_object_create(self):
        isinstance_ = isinstance(GitlabService(), GitlabService)
        self.assertEqual(isinstance_, True)


class PagureTest(TestCase):
    def test_pagure_object_create(self):
        isinstance_ = isinstance(PagureService(), PagureService)
        self.assertEqual(isinstance_, True)


class GerritTest(TestCase):
    def test_gerrit_object_create(self):
        isinstance_ = isinstance(GerritService(), GerritService)
        self.assertEqual(isinstance_, True)


if __name__ == '__main__':
    unittest.main()
