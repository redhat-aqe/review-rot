import logging

import argparse
import os

import mock
import yaml
import test_mock
import unittest
from os.path import join, dirname, expanduser, expandvars
from unittest import TestCase
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
from reviewrot.gerritstack import GerritService
from reviewrot import get_git_service, get_arguments, load_config_file
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

    def test_gitlab_object_create(self):
        self.assertTrue(isinstance((get_git_service('gitlab')), GitlabService))

    def test_request_reviews_token(self):
        with self.assertRaises(Exception) as context:
            GitlabService().request_reviews(user_name=self.config['user_name'],
                                   token=self.config['token'],
                                   host=self.config['host'])

            self.assertTrue('NewConnectionError' in str(context.exception), msg=context.exception)


    @mock.patch('gitlab.Gitlab.auth', side_effect=test_mock.mock_auth)
    @mock.patch('gitlab.Gitlab')
    def test_request_reviews_projects_get(self, mock_auth, mock_gitlab):
        with self.assertRaises(Exception) as context:
            mock_gitlab().projects.get.side_effect = test_mock.mock_projects_get()
            GitlabService().request_reviews(user_name=self.config['user_name'],
                                            repo_name=self.config['repo_name'],
                                            token=self.config['token'],
                                            host=self.config['host'])
            msg = 'Project %s not found for user %s' % (self.config['repo_name'],
                                                        self.config['user_name'])
            self.assertTrue(msg in str(context.exception), msg=context.exception)

    @mock.patch('gitlab.Gitlab.auth', side_effect=test_mock.mock_auth)
    @mock.patch('gitlab.Gitlab')
    def test_request_reviews_groups_search(self, mock_auth, mock_gitlab):
        with self.assertRaises(Exception) as context:
            mock_gitlab().groups.get.return_value = []
            GitlabService().request_reviews(user_name=self.config['user_name'],
                                            token=self.config['token'],
                                            host=self.config['host'])
            msg = 'Invalid user/group name: %s' % self.config['user_name']
            self.assertTrue(msg in str(context.exception))

    @mock.patch('gitlab.Gitlab.auth', side_effect=test_mock.mock_auth)
    @mock.patch('gitlab.Gitlab')
    @mock.patch('reviewrot.gitlabstack.GitlabService.get_reviews',
                side_effect=test_mock.mock_gitlab_get_reviews)
    def test_request_reviews_with_repo(self, mock_auth, mock_gitlab, mock_get_reviews):
        mock_gitlab().projects.get.side_effect = test_mock.mock_projects_get_()
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

    def test_pagure_avatar(self):
        expected = ('https://seccdn.libravatar.org/avatar/'
                    '9c9f7784935381befc302fe3c814f9136e7a3'
                    '3953d0318761669b8643f4df55c')
        actual = PagureService._avatar('ralph')
        self.assertEqual(actual.split('?')[0], expected)

    def test_pagure_object_create(self):
        self.assertTrue(isinstance((get_git_service('pagure')), PagureService))

    def test_request_review_incorrect_project_with_repo(self):
        pagure = PagureService()
        with self.assertRaises(Exception) as context:
            pagure.request_reviews(user_name=self.config['user_name'],
                                   repo_name=self.config['repo_name'])
        self.assertIn('Page not found', str(context.exception))


class GerritTest(TestCase):
    def setUp(self):
        filename = join(dirname(__file__), 'test_gerrittest.yaml')
        with open(filename, 'r') as f:
            self.config = yaml.load(f)

    def test_gerrit_object_create(self):
        self.assertTrue(isinstance((get_git_service('gerrit')), GerritService))

    def test_gerrit_incorrect_host_url(self):
        gerrit = GerritService()
        error_msg = self.config['incorrect_host_msg']
        with self.assertRaises(Exception)as context:
            self.assertRaises(ValueError, gerrit.request_reviews(
                repo_name=self.config['repo_name'],
                host=self.config['incorrect_host']))
        self.assertTrue(error_msg in str(context.exception))

    def test_gerrit_incorrect_repo_name(self):
        gerrit = GerritService()
        error_msg = self.config['incorrect_repo_name_msg']
        with self.assertRaises(Exception) as context:
            self.assertRaises(ValueError, gerrit.request_reviews(
                repo_name=self.config['incorrect_repo_name'],
                host=self.config['host']))
        self.assertTrue(error_msg in str(context.exception))

    def test_gerrit_request_reviews(self):
        gerrit = GerritService()
        result = gerrit.request_reviews(repo_name=self.config['repo_name'],
                                        host=self.config['host'])
        self.assertTrue(result is not None)


class CommandLineParserTest(TestCase):
    """
    Command Line Interface (CLI) Arguments will have higher precedence
    over the config file. By default, CLI arguments has False value
    for boolean expressions. In such cases, if config file arguments
    has boolean 'True' value, then 'True' value will be considered.
    """
    @classmethod
    def setUpClass(cls):
        filename = join(dirname(__file__), 'test_command_line.yaml')
        with open(filename, 'r') as f:
            cls.config = yaml.load(f)

        duration_choices = ['y', 'm', 'd', 'h', 'min']
        state_choices = ['older', 'newer']
        format_choices = ['oneline', 'indented', 'json']

        cls.choices = {'duration': duration_choices, 'state': state_choices, 'format': format_choices}

    def test_args_from_config(self):
        cli_args = argparse.Namespace(cacert=None, debug=False, format=None,
                                      insecure=False, reverse=False,
                                      duration=None, state=None, value=None)

        config_args = self.config['test1']['arguments']
        arguments = get_arguments(cli_args, config_args, self.choices)
        # arguments must contains values from config arguments

        debug_result = arguments.get('debug') == config_args.get('debug')
        format_result = arguments.get('format') == config_args.get('format')
        ssl_result = arguments.get('ssl_verify') != config_args.get('insecure')
        reverse_result = arguments.get('reverse') == config_args.get('reverse')
        group_arguments = arguments.get('state') is None and \
            arguments.get('duration') is None and \
            arguments.get('value') is None

        self.assertTrue(debug_result and reverse_result and format_result and
                        ssl_result and group_arguments)

    def test_args_from_command_line(self):
        cli_args = argparse.Namespace(cacert=None, debug=True, format='json',
                                      insecure=True, reverse=True,
                                      duration=None, state=None, value=None)

        confi_args = self.config['test2']['arguments']
        arguments = get_arguments(cli_args, confi_args, self.choices)
        # arguments must contains values from cli arguments

        debug_result = arguments.get('debug') == vars(cli_args).get('debug')
        format_result = arguments.get('format') == vars(cli_args).get('format')
        ssl_result = arguments.get('ssl_verify') is False
        reverse_result = arguments.get('reverse') == vars(cli_args).get('reverse')
        group_arguments = arguments.get('state') is None and \
            arguments.get('duration') is None and \
            arguments.get('value') is None

        self.assertTrue(debug_result and reverse_result and format_result and
                        ssl_result and group_arguments)

    def test_args_from_command_line_except_format(self):
        cli_args = argparse.Namespace(cacert=None, debug=True, format=None,
                                      insecure=False, reverse=True,
                                      duration=None, state=None, value=None)

        config_args = self.config['test3']['arguments']
        arguments = get_arguments(cli_args, config_args, self.choices)
        # All arguments must contains values from cli arguments except 'format'
        # It should be from config file

        debug_result = arguments.get('debug') is True
        format_result = arguments.get('format') == config_args.get('format')
        ssl_result = arguments.get('ssl_verify') is True
        reverse_result = arguments.get('reverse') is True
        group_arguments = arguments.get('state') is None and \
            arguments.get('duration') is None and \
            arguments.get('value') is None

        self.assertTrue(debug_result and reverse_result and format_result and
                        ssl_result and group_arguments)

    def test_grouped_args_is_none(self):
        cli_args = argparse.Namespace(cacert=None, debug=True, format=None,
                                      insecure=False, reverse=True,
                                      duration=None, state=None, value=None)

        config_args = self.config['test4']['arguments']
        arguments = get_arguments(cli_args, config_args, self.choices)
        # Only 'state' and 'duration' is given in config, but 'value' is not.
        # So value of all grouped arguments should be None

        group_arguments = arguments.get('state') is None and \
            arguments.get('duration') is None and \
            arguments.get('value') is None

        self.assertTrue(group_arguments)

    def test_grouped_args_from_config(self):
        cli_args = argparse.Namespace(cacert=None, debug=True, format=None,
                                      insecure=False, reverse=True,
                                      duration=None, state=None, value=None)

        config_args = self.config['test5']['arguments']
        arguments = get_arguments(cli_args, config_args, self.choices)
        # Arguments 'state', 'duration' and 'value' are given in config. So
        # value of all grouped arguments should taken from config file. Grouped
        # argument's (state', 'duration', 'value) values given by CLI are None
        group_arguments = arguments.get('state') == config_args.get('state') \
            and arguments.get('duration') == config_args.get('duration') and \
            arguments.get('value') == config_args.get('value')

        self.assertTrue(group_arguments)

    def test_grouped_args_from_command_line(self):
        cli_args = argparse.Namespace(cacert=None, debug=True, format=None,
                                      insecure=False, reverse=True,
                                      duration=10, state='older', value='m')

        config_args = self.config['test6']['arguments']
        arguments = get_arguments(cli_args, config_args, self.choices)
        # Arguments 'state', 'duration' and 'value' is given in config. Grouped
        # argument (state', 'duration', 'value) values are also given as CLI
        # arguments. So value of all grouped arguments should taken from CLI

        group_arguments = arguments.get('state') == vars(cli_args).get('state')\
            and arguments.get('duration') == vars(cli_args).get('duration')\
            and arguments.get('value') == vars(cli_args).get('value')

        self.assertTrue(group_arguments)

    def test_args_ca_certi_invalid_path_from_config(self):
        cli_args = argparse.Namespace(cacert=None, debug=False, format=None,
                                      insecure=False, reverse=False,
                                      duration=None, state=None, value=None)

        config_args = self.config['test7']['arguments']
        with self.assertRaises(IOError) as context:
            arguments = get_arguments(cli_args, config_args, self.choices)
            msg = "No certificate file found "
            self.assertTrue(msg in str(context.exception), msg=context.exception)



    def test_args_ca_certi_invalid_path_from_command_line(self):
        cli_args = argparse.Namespace(cacert="~/review-rot/", debug=False,
                                      format=None, insecure=False,
                                      reverse=False, duration=None, state=None,
                                      value=None)

        config_args = self.config['test8']['arguments']
        with self.assertRaises(IOError) as context:
            arguments = get_arguments(cli_args, config_args, self.choices)
            msg = "No certificate file found "
            self.assertTrue(msg in str(context.exception), msg=context.exception)

    def test_args_cacert_with_insecure(self):
        cli_args = argparse.Namespace(cacert=None, debug=False, format=None,
                                      insecure=False, reverse=False,
                                      duration=None, state=None, value=None)
        config_args = self.config['test9']['arguments']
        with self.assertRaises(ValueError) as context:
            arguments = get_arguments(cli_args, config_args, self.choices)
            msg = "Certificate file can't be used with insecure flag"
            self.assertTrue(msg in str(context.exception), msg=context.exception)

    @mock.patch('__builtin__.raw_input', return_value='n')
    def test_load_config_file_re_write_no(self, mocked_input):
        filename = join(dirname(__file__), 'test_old_format.yaml')
        load_config_file(filename)
        # Load the old style config file and don't convert it to
        # new style dict format.
        with open(filename, 'r') as f:
            new_config = yaml.load(f)

        arguments_present = 'arguments' not in new_config
        git_services_present = 'type' in new_config[0]
        self.assertTrue(isinstance(new_config, list) and arguments_present
                         and git_services_present)

    @mock.patch('__builtin__.raw_input', return_value='y')
    def test_load_config_file_re_write_yes(self, mocked_input):
        filename = join(dirname(__file__), 'test_old_format.yaml')
        load_config_file(filename)
        # Load the old style config file and converts it to new style
        # dict format. Also creates backup file before converting.
        with open(filename, 'r') as f:
            new_config = yaml.load(f)

        backup_config_file_exist = os.path.exists(filename + ".backup")
        arguments_present = 'arguments' in new_config
        git_services_present = 'git_services' in new_config
        self.assertTrue(isinstance(new_config, dict) and arguments_present
                        and git_services_present and backup_config_file_exist)

    @classmethod
    def tearDownClass(cls):
        backup_filename = join(dirname(__file__), 'test_old_format.yaml.backup')
        filename = join(dirname(__file__), 'test_old_format.yaml')
        if os.path.exists(filename):
            os.remove(filename)
            os.rename(backup_filename,filename)

if __name__ == '__main__':
    unittest.main()