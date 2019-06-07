import logging
import argparse
import os
import mock
import yaml
import test_mock
import unittest
from os.path import join, dirname
from unittest import TestCase
from six.moves import urllib
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
from reviewrot.gerritstack import GerritService
from reviewrot.phabricatorstack import PhabricatorService
from reviewrot import get_git_service, get_arguments, load_config_file
from github.GithubException import BadCredentialsException
from reviewrot.basereview import LastComment
import datetime
from phabricator import Phabricator


# Disable logging to avoid messing up test output
logging.disable(logging.CRITICAL)


class PhabricatorTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), "test_phabricatortest.yaml")
        with open(filename, "r") as f:
            self.config = yaml.safe_load(f)

    def test_object_create(self):
        self.assertTrue(isinstance((get_git_service("phabricator")),
                                   PhabricatorService))

    def test_request_review_token(self):
        service = PhabricatorService()
        with self.assertRaises(Exception) as context:
            service.request_reviews(host=self.config["host"],
                                    token=self.config["token"])
        res = len(str(context.exception)) > 0
        self.assertTrue(res)

    @mock.patch('phabricator.Phabricator.update_interfaces',
                side_effect=test_mock.mock_phabricator_update_interfaces)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.get_reviews',
                side_effect=test_mock.mock_phabricator_get_reviews)
    @mock.patch(
        'reviewrot.phabricatorstack.PhabricatorService.differential_query',
        side_effect=test_mock.mock_phabricator_differential_query)
    def test_request_reviews_no_repo(
            self,
            mock_phabricator_update_interfaces,
            mock_phabricator_get_reviews,
            mock_phabricator_differential_query_no_repos):
        response = PhabricatorService().request_reviews(
            host=self.config['host'],
            token=self.config['token'],
            repo_name=None
        )
        self.assertEqual(response[0]._format_oneline(1, 1),
                         self.config['msg1'])

    @mock.patch('phabricator.Phabricator.update_interfaces',
                side_effect=test_mock.mock_phabricator_update_interfaces)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.get_reviews',
                side_effect=test_mock.mock_phabricator_get_reviews)
    @mock.patch(
        'reviewrot.phabricatorstack.PhabricatorService.differential_query',
        side_effect=test_mock.mock_phabricator_differential_query)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.author_data',
                side_effect=test_mock.mock_phabricator_author_data)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.time_from_epoch',
                side_effect=test_mock.mock_phabricator_time_from_epoch)
    def test_request_reviews_with_repos(
            self,
            mock_phabricator_update_interfaces,
            mock_phabricator_get_reviews,
            mock_phabricator_differential_query_no_repos,
            mock_phabricator_author_data,
            mock_phabricator_time_from_epoch):
        response = PhabricatorService().request_reviews(
            host=self.config['host'],
            token=self.config['token'],
            repo_name=["dummy_user"]
        )
        self.assertEqual(response[0]._format_oneline(1, 1),
                         self.config['msg1'])

    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.user_query_ids',
                side_effect=test_mock.mock_phabricator_user_query_ids)
    def test_author_data_empty(
            self,
            mock_phabricator_user_query_ids):
        phab = Phabricator(host='dummmy.com', token='dummy.token')
        response, raw_response = PhabricatorService().author_data(
            author_phid="1234",
            raw_response=[],
            phab=phab)
        self.assertTrue(response['userName'] == 'dummy_user')

    def test_author_data_full(
            self):
        phab = Phabricator(host='dummmy.com', token='dummy.token')
        response, raw_response = PhabricatorService().author_data(
            author_phid="PHID-USER-test",
            raw_response=test_mock.mock_phabricator_raw_response(),
            phab=phab)
        print(response)
        self.assertTrue(True, False)

    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.get_comments',
                side_effect=test_mock.mock_phabricator_get_comments)
    @mock.patch(
        'reviewrot.phabricatorstack.PhabricatorService.get_last_comment',
        side_effect=test_mock.mock_phabricator_get_last_comment)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.author_data',
                side_effect=test_mock.mock_phabricator_author_data)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.time_from_epoch',
                side_effect=test_mock.mock_phabricator_time_from_epoch)
    def test_get_reviews_no_raw(self, mock_get_comments,
                         mock_phabricator_get_last_comment,
                         mock_phabricator_author_data,
                         mock_phabricator_time_from_epoch):
        reviews = test_mock.mock_phabricator_differential_query(
            None, None, None)
        phab = Phabricator(host='dummmy.com', token='dummy.token')
        response = PhabricatorService().get_reviews(phab, reviews,
                                                    host="www.google.com",
                                                    raw_response=[])
        self.assertEqual(response[0]._format_oneline(1, 1),
                         self.config['msg2'])

    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.get_comments',
                side_effect=test_mock.mock_phabricator_get_comments_)
    @mock.patch(
        'reviewrot.phabricatorstack.PhabricatorService.get_last_comment',
        side_effect=test_mock.mock_phabricator_get_last_comment)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.author_data',
                side_effect=test_mock.mock_phabricator_author_data)
    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.time_from_epoch',
                side_effect=test_mock.mock_phabricator_time_from_epoch)
    def test_get_reviews_last_comment(self, mock_phabricator_get_comments_,
                                      mock_phabricator_get_last_comment,
                                      mock_phabricator_author_data,
                                      mock_datetime_fromtimestamp):
        reviews = test_mock.mock_phabricator_differential_query(
            None, None, None)
        phab = Phabricator(host='dummmy.com', token='dummy.token')
        response = PhabricatorService().get_reviews(
            phab,
            reviews,
            host="www.google.com",
            show_last_comment=True,
            raw_response=[])
        self.assertEqual(response[0]._format_oneline(1, 1),
                         self.config['msg3'])

    @mock.patch('reviewrot.phabricatorstack.PhabricatorService.author_data',
                side_effect=test_mock.mock_phabricator_author_data)
    def test_get_last_comment(self, mock_phabricator_author_data):
        phab = Phabricator(host='dummy.com', token='dummy.token')
        comments = test_mock.mock_phabricator_get_comments(1201, phab)
        response = PhabricatorService().get_last_comment(comments, phab, raw_response=[])
        createdAt = datetime.datetime.fromtimestamp(float(1551763640))
        res = LastComment(author='dummy_user',
                          body='This is some content',
                          created_at=createdAt)
        self.assertEqual(response, res)


class GithubTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), "test_githubtest.yaml")
        with open(filename, "r") as f:
            self.config = yaml.safe_load(f)

    def test_object_create(self):
        self.assertTrue(isinstance((get_git_service("github")), GithubService))

    def test_request_review_token(self):
        github = GithubService()
        with self.assertRaises(BadCredentialsException) as context:
            github.request_reviews(
                user_name=self.config["user_name"], token=self.config["token"]
            )
        self.assertTrue("Bad credentials" in str(context.exception))

    @mock.patch("github.Github.get_user", side_effect=test_mock.mock_get_user)
    def test_request_reviews_get_user(self, mock_get_user):
        with self.assertRaises(Exception) as context:
            GithubService().request_reviews(
                user_name=self.config["user_name"], token=self.config["token"]
            )
        msg = "Invalid username/organizaton: %s" % self.config["user_name"]
        self.assertTrue(msg in str(context.exception))

    @mock.patch("github.Github.get_user", side_effect=test_mock.mock_get_user_)
    @mock.patch(
        "reviewrot.githubstack.GithubService.get_reviews",
        side_effect=test_mock.mock_github_get_reviews,
    )
    def test_request_reviews_with_repo(
        self, mock_get_user_, mock_github_get_reviews
    ):
        res = GithubService().request_reviews(
            user_name=self.config["user_name"],
            token=self.config["token"],
            repo_name=self.config["repo_name"],
        )
        self.assertEqual([self.config["msg"]], res)

    @mock.patch("github.Github.get_user", side_effect=test_mock.mock_get_user_)
    @mock.patch(
        "github.NamedUser.NamedUser.get_repos",
        side_effect=test_mock.mock_get_repos,
    )
    @mock.patch(
        "reviewrot.githubstack.GithubService.get_reviews",
        side_effect=test_mock.mock_github_get_reviews,
    )
    def test_request_reviews_without_repo(
        self, mock_get_user_, mock_github_get_reviews, mock_get_repos
    ):
        res = GithubService().request_reviews(
            user_name=self.config["user_name"], token=self.config["token"]
        )
        self.assertEqual([self.config["msg"]], res)

    @mock.patch(
        "github.NamedUser.NamedUser.get_repo",
        side_effect=test_mock.mock_get_repo,
    )
    def test_get_reviews_get_repo_not_found(self, mock_get_repo):
        with self.assertRaises(Exception) as context:
            uname = test_mock.mock_get_user_(self.config["user_name"])
            GithubService().get_reviews(
                uname=uname, repo_name=self.config["repo_name"]
            )
        msg = "Repository %s not found for user %s" % (
            self.config["repo_name"],
            uname.login,
        )
        self.assertTrue(msg in str(context.exception))

    @mock.patch(
        "github.NamedUser.NamedUser.get_repo",
        side_effect=test_mock.mock_get_repo_,
    )
    @mock.patch(
        "github.Repository.Repository.get_pulls",
        side_effect=test_mock.mock_get_pulls,
    )
    def test_get_reviews_get_repo(self, mock_get_pulls, mock_get_repo_):
        uname = test_mock.mock_get_user_(self.config["user_name"])
        res = GithubService().get_reviews(
            uname=uname, repo_name=self.config["repo_name"]
        )
        self.assertEqual(res, [])

    @mock.patch("github.PullRequest")
    def test_get_last_comment_containing_review_comment(self, mock_pr):
        github = GithubService()
        now = datetime.datetime.now()

        review_comment = test_mock.FakeGithubComment(
            author="user", body="a review comment", created_at=now
        )

        mock_pr.get_comments.return_value = test_mock.FakeGithubPaginatedList(
            comments=[review_comment]
        )
        mock_pr.get_issue_comments.return_value = test_mock.FakeGithubPaginatedList(
            comments=[]
        )

        last_comment = github.get_last_comment(mock_pr)
        self.assertEqual(
            last_comment,
            LastComment(
                author="user", body="a review comment", created_at=now
            ),
        )

    @mock.patch("github.PullRequest")
    def test_get_last_comment_containing_issue_comment(self, mock_pr):
        github = GithubService()
        now = datetime.datetime.now()

        issue_comment = test_mock.FakeGithubComment(
            author="user", body="a issue comment", created_at=now
        )

        mock_pr.get_comments.return_value = test_mock.FakeGithubPaginatedList(
            comments=[]
        )
        mock_pr.get_issue_comments.return_value = test_mock.FakeGithubPaginatedList(
            comments=[issue_comment]
        )

        last_comment = github.get_last_comment(mock_pr)
        self.assertEqual(
            last_comment,
            LastComment(author="user", body="a issue comment", created_at=now),
        )

    @mock.patch("github.PullRequest")
    def test_get_last_comment_containing_both_types_of_comments(self, mock_pr):

        github = GithubService()
        now = datetime.datetime.now()

        review_comment = test_mock.FakeGithubComment(
            author="user",
            body="a review comment",
            created_at=now - datetime.timedelta(minutes=1),
        )
        issue_comment = test_mock.FakeGithubComment(
            author="user2", body="last issue comment", created_at=now
        )

        mock_pr.get_comments.return_value = test_mock.FakeGithubPaginatedList(
            comments=[review_comment]
        )
        mock_pr.get_issue_comments.return_value = test_mock.FakeGithubPaginatedList(
            comments=[issue_comment]
        )

        last_comment = github.get_last_comment(mock_pr)
        self.assertEqual(
            last_comment,
            LastComment(
                author="user2", body="last issue comment", created_at=now
            ),
        )


class GitlabTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), "test_gitlabtest.yaml")
        with open(filename, "r") as f:
            self.config = yaml.safe_load(f)

    def test_gitlab_object_create(self):
        self.assertTrue(isinstance((get_git_service("gitlab")), GitlabService))

    def test_request_reviews_token(self):
        with self.assertRaises(Exception) as context:
            GitlabService().request_reviews(
                user_name=self.config["user_name"],
                token=self.config["token"],
                host=self.config["host"],
            )

            self.assertTrue(
                "NewConnectionError" in str(context.exception),
                msg=context.exception,
            )

    @mock.patch("gitlab.Gitlab.auth", side_effect=test_mock.mock_auth)
    @mock.patch("gitlab.Gitlab")
    def test_request_reviews_projects_get(self, mock_auth, mock_gitlab):
        with self.assertRaises(Exception) as context:
            mock_gitlab().projects.get.side_effect = (
                test_mock.mock_projects_get()
            )
            GitlabService().request_reviews(
                user_name=self.config["user_name"],
                repo_name=self.config["repo_name"],
                token=self.config["token"],
                host=self.config["host"],
            )
            msg = "Project %s not found for user %s" % (
                self.config["repo_name"],
                self.config["user_name"],
            )
            self.assertTrue(
                msg in str(context.exception), msg=context.exception
            )

    @mock.patch("gitlab.Gitlab.auth", side_effect=test_mock.mock_auth)
    @mock.patch("gitlab.Gitlab")
    def test_request_reviews_groups_search(self, mock_auth, mock_gitlab):
        with self.assertRaises(Exception) as context:
            mock_gitlab().groups.get.return_value = []
            GitlabService().request_reviews(
                user_name=self.config["user_name"],
                token=self.config["token"],
                host=self.config["host"],
            )
            msg = "Invalid user/group name: %s" % self.config["user_name"]
            self.assertTrue(msg in str(context.exception))

    @mock.patch("gitlab.Gitlab.auth", side_effect=test_mock.mock_auth)
    @mock.patch("gitlab.Gitlab")
    @mock.patch(
        "reviewrot.gitlabstack.GitlabService.get_reviews",
        side_effect=test_mock.mock_gitlab_get_reviews,
    )
    def test_request_reviews_with_repo(
        self, mock_auth, mock_gitlab, mock_get_reviews
    ):
        mock_gitlab().projects.get.side_effect = test_mock.mock_projects_get_()
        res = GitlabService().request_reviews(
            user_name=self.config["user_name"],
            repo_name=self.config["repo_name"],
            token=self.config["token"],
            host=self.config["host"],
        )
        self.assertEqual([self.config["msg"]], res)

    @mock.patch("gitlab.v4.objects.ProjectMergeRequest")
    def test_get_last_comment(self, mock_mr):
        gitlab = GitlabService()

        now = datetime.datetime.now()

        mock_mr.notes.list.return_value = [
            test_mock.FakeProjectMergeRequestNote(
                system=True,
                author="Gitlab",
                created_at=now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                body="System comment",
            ),
            test_mock.FakeProjectMergeRequestNote(
                system=False,
                author="user",
                created_at=now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                body="last comment by user",
            ),
            test_mock.FakeProjectMergeRequestNote(
                system=False,
                author="user2",
                created_at=(now - datetime.timedelta(minutes=1)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                body="user comment",
            ),
        ]

        last_comment = gitlab.get_last_comment(mock_mr)
        self.assertEqual(
            last_comment,
            LastComment(
                author="user", body="last comment by user", created_at=now
            ),
        )


class PagureTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), "test_paguretest.yaml")
        with open(filename, "r") as f:
            self.config = yaml.safe_load(f)

    @mock.patch("reviewrot.pagurestack.PagureService._call_api")
    def test_pagure_missing_avatar(self, mock_call_api):
        mock_call_api.return_value = {}
        expected = (
            "https://seccdn.libravatar.org/avatar/"
            "9c9f7784935381befc302fe3c814f9136e7a33953d0318761669b8643f4df55c"
        )
        actual = PagureService()._avatar("ralph")
        self.assertEqual(actual.split("?")[0], expected)

    @mock.patch("reviewrot.pagurestack.PagureService._call_api")
    def test_pagure_missing_avatar(self, mock_call_api):
        base_avatar_url = (
            "https://seccdn.libravatar.org/avatar/"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbccccccccccccccc"
        )
        pagure_avatar_url = base_avatar_url + "?s=16&d=retro"
        mock_call_api.return_value = {'user': {'avatar_url': pagure_avatar_url}}

        expected_query = "s=64&d=retro"
        expected = base_avatar_url + "?" + expected_query

        actual = PagureService()._avatar("ralph")
        self.assertEqual(actual.split("?")[0], base_avatar_url)
        actual_query = urllib.parse.parse_qs(urllib.parse.urlparse(actual).query)
        self.assertEqual(actual_query, urllib.parse.parse_qs(expected_query))

    def test_pagure_object_create(self):
        self.assertTrue(isinstance((get_git_service("pagure")), PagureService))

    def test_request_review_incorrect_project_with_repo(self):
        pagure = PagureService()
        with self.assertRaises(Exception) as context:
            pagure.request_reviews(
                user_name=self.config["user_name"],
                repo_name=self.config["repo_name"],
            )
            self.assertIn("Page not found", str(context.exception))

    def test_get_last_comment(self):
        pagure = PagureService()
        res = {
            "comments": [
                {
                    "comment": "first comment",
                    "date_created": "1539776992",
                    "user1": {"name": "username"},
                },
                {
                    "comment": "last comment",
                    "date_created": "1539777081",
                    "user": {"name": "user2"},
                },
            ]
        }

        last_comment = pagure.get_last_comment(res)
        self.assertEqual(
            last_comment,
            LastComment(
                author="user2",
                body="last comment",
                created_at=datetime.datetime.utcfromtimestamp(1539777081),
            ),
        )


class GerritTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), "test_gerrittest.yaml")
        with open(filename, "r") as f:
            self.config = yaml.safe_load(f)

    def test_gerrit_object_create(self):
        self.assertTrue(isinstance((get_git_service("gerrit")), GerritService))

    def test_gerrit_incorrect_host_url(self):
        gerrit = GerritService()
        error_msg = self.config["incorrect_host_msg"]
        with self.assertRaises(Exception) as context:
            self.assertRaises(
                ValueError,
                gerrit.request_reviews(
                    repo_name=self.config["repo_name"],
                    host=self.config["incorrect_host"],
                ),
            )
            self.assertTrue(error_msg in str(context.exception))

    def test_gerrit_incorrect_repo_name(self):
        gerrit = GerritService()
        error_msg = self.config["incorrect_repo_name_msg"]
        with self.assertRaises(Exception) as context:
            self.assertRaises(
                ValueError,
                gerrit.request_reviews(
                    repo_name=self.config["incorrect_repo_name"],
                    host=self.config["host"],
                ),
            )
            self.assertTrue(error_msg in str(context.exception))

    def test_gerrit_request_reviews(self):
        gerrit = GerritService()
        result = gerrit.request_reviews(
            repo_name=self.config["repo_name"], host=self.config["host"]
        )
        self.assertTrue(result is not None)

    def test_get_last_comment(self):
        gerrit = GerritService()
        now = datetime.datetime.now()

        comments_response = {
            u"file1.py": [
                {
                    u"author": {
                        u"username": u"user1",
                        u"email": u"user1@example.com",
                    },
                    u"updated": now.strftime("%Y-%m-%d %H:%M:%S.%f000"),
                    u"message": u"last comment in file1.py",
                }
            ],
            u"file2.py": [
                {
                    u"author": {
                        u"username": u"user2",
                        u"email": u"user2@example.com",
                    },
                    u"updated": (now - datetime.timedelta(days=1)).strftime(
                        "%Y-%m-%d %H:%M:%S.%f000"
                    ),
                    u"message": u"#1 comment",
                },
                {
                    u"author": {
                        u"username": u"user3",
                        u"email": u"user3@example.com",
                    },
                    u"updated": (now - datetime.timedelta(minutes=1)).strftime(
                        "%Y-%m-%d %H:%M:%S.%f000"
                    ),
                    u"message": u"last comment in file2.py",
                },
            ],
        }

        last_comment = gerrit.get_last_comment(comments_response)
        self.assertEqual(
            last_comment,
            LastComment(
                author="user1", body="last comment in file1.py", created_at=now
            ),
        )


class CommandLineParserTest(TestCase):
    """
    Command Line Interface (CLI) Arguments will have higher precedence
    over the config file. By default, CLI arguments has False value
    for boolean expressions. In such cases, if config file arguments
    has boolean 'True' value, then 'True' value will be considered.
    """

    @classmethod
    def setUpClass(cls):
        filename = join(dirname(__file__), "test_command_line.yaml")
        with open(filename, "r") as f:
            cls.config = yaml.safe_load(f)

        duration_choices = ["y", "m", "d", "h", "min"]
        state_choices = ["older", "newer"]
        format_choices = ["oneline", "indented", "json"]

        cls.choices = {
            "duration": duration_choices,
            "state": state_choices,
            "format": format_choices,
        }

    def test_args_from_config(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=False,
            format=None,
            insecure=False,
            reverse=False,
            duration=None,
            state=None,
            value=None,
            sort=None,
        )

        config = self.config["test1"]
        config_args = self.config["test1"]["arguments"]
        arguments = get_arguments(
            cli_args, config, self.choices
        )
        # arguments must contains values from config arguments

        debug_result = arguments.get("debug") == config_args.get("debug")
        format_result = arguments.get("format") == config_args.get("format")
        ssl_result = arguments.get("ssl_verify") != config_args.get("insecure")
        reverse_result = arguments.get("reverse") == config_args.get("reverse")
        group_arguments = (
            arguments.get("state") is None
            and arguments.get("duration") is None
            and arguments.get("value") is None
        )
        sort_result = arguments.get("sort") == config_args.get("sort")

        self.assertTrue(
            debug_result
            and reverse_result
            and format_result
            and ssl_result
            and group_arguments
            and sort_result
        )

    def test_args_from_command_line(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format="json",
            insecure=True,
            reverse=True,
            duration=None,
            state=None,
            value=None,
            sort='updated',
        )

        config = self.config["test2"]
        arguments = get_arguments(
            cli_args, config, self.choices
        )
        # arguments must contains values from cli arguments

        debug_result = arguments.get("debug") == vars(cli_args).get("debug")
        format_result = arguments.get("format") == vars(cli_args).get("format")
        ssl_result = arguments.get("ssl_verify") is False
        reverse_result = arguments.get("reverse") == vars(cli_args).get(
            "reverse"
        )
        group_arguments = (
            arguments.get("state") is None
            and arguments.get("duration") is None
            and arguments.get("value") is None
        )
        sort_result = arguments.get("sort") == vars(cli_args).get('sort')

        self.assertTrue(
            debug_result
            and reverse_result
            and format_result
            and ssl_result
            and group_arguments
            and sort_result
        )

    def test_args_from_command_line_except_format(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format=None,
            insecure=False,
            reverse=True,
            duration=None,
            state=None,
            value=None,
            sort=None,
        )

        config = self.config["test3"]
        config_args = self.config["test3"]["arguments"]
        arguments = get_arguments(
            cli_args, config, self.choices
        )
        # All arguments must contains values from cli arguments except 'format'
        # It should be from config file

        debug_result = arguments.get("debug") is True
        format_result = arguments.get("format") == config_args.get("format")
        ssl_result = arguments.get("ssl_verify") is True
        reverse_result = arguments.get("reverse") is True
        group_arguments = (
            arguments.get("state") is None
            and arguments.get("duration") is None
            and arguments.get("value") is None
        )
        sort_result = arguments.get('sort') is None

        self.assertTrue(
            debug_result
            and reverse_result
            and format_result
            and ssl_result
            and group_arguments
        )

    def test_grouped_args_is_none(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format=None,
            insecure=False,
            reverse=True,
            duration=None,
            state=None,
            value=None,
        )

        config = self.config["test4"]
        arguments = get_arguments(
            cli_args, config, self.choices
        )
        # Only 'state' and 'duration' is given in config, but 'value' is not.
        # So value of all grouped arguments should be None

        group_arguments = (
            arguments.get("state") is None
            and arguments.get("duration") is None
            and arguments.get("value") is None
        )

        self.assertTrue(group_arguments)

    def test_grouped_args_from_config(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format=None,
            insecure=False,
            reverse=True,
            duration=None,
            state=None,
            value=None,
        )

        config = self.config["test5"]
        config_args = self.config["test5"]["arguments"]
        arguments = get_arguments(
            cli_args, config, self.choices
        )
        # Arguments 'state', 'duration' and 'value' are given in config. So
        # value of all grouped arguments should taken from config file. Grouped
        # argument's (state', 'duration', 'value) values given by CLI are None
        group_arguments = (
            arguments.get("state") == config_args.get("state")
            and arguments.get("duration") == config_args.get("duration")
            and arguments.get("value") == config_args.get("value")
        )

        self.assertTrue(group_arguments)

    def test_grouped_args_from_command_line(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format=None,
            insecure=False,
            reverse=True,
            duration=10,
            state="older",
            value="m",
        )

        config = self.config["test6"]
        arguments = get_arguments(
            cli_args, config, choices=self.choices
        )
        # Arguments 'state', 'duration' and 'value' is given in config. Grouped
        # argument (state', 'duration', 'value) values are also given as CLI
        # arguments. So value of all grouped arguments should taken from CLI

        group_arguments = (
            arguments.get("state") == vars(cli_args).get("state")
            and arguments.get("duration") == vars(cli_args).get("duration")
            and arguments.get("value") == vars(cli_args).get("value")
        )

        self.assertTrue(group_arguments)

    def test_args_ca_certi_invalid_path_from_config(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=False,
            format=None,
            insecure=False,
            reverse=False,
            duration=None,
            state=None,
            value=None,
        )

        config = self.config["test7"]
        with self.assertRaises(IOError) as context:
            get_arguments(
                cli_args, config, self.choices
            )
            msg = "No certificate file found "
            self.assertTrue(
                msg in str(context.exception), msg=context.exception
            )

    def test_args_ca_certi_invalid_path_from_command_line(self):
        cli_args = argparse.Namespace(
            cacert="~/review-rot/",
            debug=False,
            format=None,
            insecure=False,
            reverse=False,
            duration=None,
            state=None,
            value=None,
        )

        config = self.config["test8"]
        with self.assertRaises(IOError) as context:
            get_arguments(
                cli_args, config, self.choices
            )
            msg = "No certificate file found "
            self.assertTrue(
                msg in str(context.exception), msg=context.exception
            )

    def test_args_cacert_with_insecure(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=False,
            format=None,
            insecure=False,
            reverse=False,
            duration=None,
            state=None,
            value=None,
        )
        config = self.config["test9"]
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_args, config, self.choices
            )
            msg = "Certificate file can't be used with insecure flag"
            self.assertTrue(
                msg in str(context.exception), msg=context.exception
            )

    @mock.patch("reviewrot.input", return_value="n")
    def test_load_config_file_re_write_no(self, mocked_input):
        filename = join(dirname(__file__), "test_old_format.yaml")
        load_config_file(filename)
        # Load the old style config file and don't convert it to
        # new style dict format.
        with open(filename, "r") as f:
            new_config = yaml.safe_load(f)

        arguments_present = "arguments" not in new_config
        git_services_present = "type" in new_config[0]
        self.assertTrue(
            isinstance(new_config, list)
            and arguments_present
            and git_services_present
        )

    @mock.patch("reviewrot.input", return_value="y")
    def test_load_config_file_re_write_yes(self, mocked_input):
        filename = join(dirname(__file__), "test_old_format.yaml")
        load_config_file(filename)
        # Load the old style config file and converts it to new style
        # dict format. Also creates backup file before converting.
        with open(filename, "r") as f:
            new_config = yaml.safe_load(f)

        backup_config_file_exist = os.path.exists(filename + ".backup")
        arguments_present = "arguments" in new_config
        git_services_present = "git_services" in new_config
        self.assertTrue(
            isinstance(new_config, dict)
            and arguments_present
            and git_services_present
            and backup_config_file_exist
        )

    def test_invalid_combination_format_and_email_command_line(self):
        cli_args = argparse.Namespace(
            format="json", email="some@email.com", insecure=False, cacert=None
        )
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config={},
                choices=self.choices,
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

    def test_invalid_combination_format_and_show_last_comment_command_line(
        self
    ):

        cli_args = argparse.Namespace(
            format="oneline", show_last_comment=0, insecure=False, cacert=None
        )
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config={},
                choices=self.choices,
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

        cli_args = argparse.Namespace(
            format="indented", show_last_comment=0, insecure=False, cacert=None
        )
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config={},
                choices=self.choices,
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

    def test_invalid_combination_format_and_email_config_file(self):
        cli_args = argparse.Namespace(insecure=False, cacert=None)

        config = {
            "arguments": {
                "email": "some@email",
                "format": "json"
            }
        }
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config=config,
                choices=self.choices,
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

    def test_invalid_combination_format_and_show_last_comment_configfile(self):
        cli_args = argparse.Namespace(insecure=False, cacert=None)
        config = {
            "arguments": {
                "format": "oneline",
                "show_last_comment": 0
            }
        }
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config=config,
                choices=self.choices,
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

        config = {
            "arguments": {
                "format": "indented",
                "show_last_comment": 0
            }
        }
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config=config,
                choices=self.choices,
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

    def test_email_argument_in_config(self):
        cli_args = argparse.Namespace(cacert=None, insecure=False)
        email_input = (
            "user@example.com, user2@example.com,"
            "       user3@example.com,user4@example.com"
        )
        config = {
            "arguments": {
                "email": email_input
            },
            "mailer": {
                "sender": "do-not-reply@example.com",
                "server": "smtp.example.com",
            }
        }

        arguments = get_arguments(
            cli_args, config, self.choices
        )

        self.assertEqual(
            arguments.get("email"),
            [
                "user@example.com",
                "user2@example.com",
                "user3@example.com",
                "user4@example.com",
            ],
        )

    def test_email_functionality_without_mailer_configuration(self):
        cli_args = argparse.Namespace(cacert=None, insecure=False)
        config = {
            "arguments": {
                "email": "email@example.com"
            }
        }

        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_args, config, choices=self.choices
            )
            msg = "Missing mailer configuration. " \
                  "Check examples/sampleinput_email.yaml " \
                  "for correct configuration."

            self.assertTrue(msg in str(context.exception))

    def test_invalid_combination_format_and_irc_command_line(self):
        cli_args = argparse.Namespace(
            format="json", irc=True, insecure=False, cacert=None
        )
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config={},
                choices=self.choices,
            )
            msg = "No format should be specified when selecting irc output"

            self.assertTrue(msg in str(context.exception))

    def test_invalid_combination_format_and_irc_config_file(self):
        cli_args = argparse.Namespace(insecure=False, cacert=None)

        config = {
            "arguments": {
                "irc": "#channel1",
                "format": "json"
            },
            "irc": {
                "server": "irc.example.com",
                "port": 12345,
            }
        }
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config=config,
                choices=self.choices,
            )
            msg = "No format should be specified when selecting irc output"

            self.assertTrue(msg in str(context.exception))

    def test_irc_functionality_without_irc_configuration(self):
        cli_args = argparse.Namespace(cacert=None, insecure=False)
        config = {
            "arguments": {
                "irc": "#channel1"
            }
        }

        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_args, config, choices=self.choices
            )
            msg = "Missing irc configuration. " \
                  "Check examples/sampleinput_irc.yaml " \
                  "for correct configuration."

            self.assertTrue(msg in str(context.exception))

    def test_irc_argument_in_config(self):
        cli_args = argparse.Namespace(cacert=None, insecure=False)
        irc_channels = (
            "#channel1, #channel2,"
            "       #channel3,#channel4"
        )
        config = {
            "arguments": {
                "irc": irc_channels
            },
            "irc": {
                "server": "irc.example.com",
                "port": 12345,
            }
        }

        arguments = get_arguments(
            cli_args, config, self.choices
        )

        self.assertEqual(
            arguments.get("irc"),
            [
                "#channel1",
                "#channel2",
                "#channel3",
                "#channel4",
            ],
        )

    @classmethod
    def tearDownClass(cls):
        backup_filename = join(
            dirname(__file__), "test_old_format.yaml.backup"
        )
        filename = join(dirname(__file__), "test_old_format.yaml")
        if os.path.exists(filename):
            os.remove(filename)
            os.rename(backup_filename, filename)


if __name__ == "__main__":
    unittest.main()
