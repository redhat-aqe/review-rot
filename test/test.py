import logging
import argparse
import os
import mock
import yaml
import test_mock
import unittest
import datetime
from os.path import join, dirname
from unittest import TestCase
from six.moves import urllib
from reviewrot.pagurestack import PagureService
from reviewrot.gerritstack import GerritService
from dateutil.relativedelta import relativedelta
from reviewrot.basereview import LastComment, BaseService, Age
from reviewrot import (
    get_git_service,
    get_arguments,
    load_config_file,
    remove_wip,
    ParseAge,
    parse_cli_args,
)


# Disable logging to avoid messing up test output
logging.disable(logging.CRITICAL)


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

    def test_args_from_config(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=False,
            format=None,
            insecure=False,
            reverse=False,
            age=None,
            sort=None,
        )

        config = self.config["test1"]
        config_args = self.config["test1"]["arguments"]
        arguments = get_arguments(
            cli_args, config
        )
        # arguments must contains values from config arguments

        debug_result = arguments.get("debug") == config_args.get("debug")
        format_result = arguments.get("format") == config_args.get("format")
        ssl_result = arguments.get("ssl_verify") != config_args.get("insecure")
        reverse_result = arguments.get("reverse") == config_args.get("reverse")
        age_result = arguments.get('age') == config_args.get('age')
        sort_result = arguments.get("sort") == config_args.get("sort")

        self.assertTrue(
            debug_result
            and reverse_result
            and format_result
            and age_result
            and ssl_result
            and sort_result
        )

    def test_args_from_command_line(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format="json",
            insecure=True,
            reverse=True,
            age=None,
            sort='updated',
        )

        config = self.config["test2"]
        arguments = get_arguments(
            cli_args, config
        )
        # arguments must contains values from cli arguments

        debug_result = arguments.get("debug") == vars(cli_args).get("debug")
        format_result = arguments.get("format") == vars(cli_args).get("format")
        ssl_result = arguments.get("ssl_verify") is False
        reverse_result = arguments.get("reverse") == vars(cli_args).get(
            "reverse"
        )
        age = arguments.get('age') is None
        sort_result = arguments.get("sort") == vars(cli_args).get('sort')

        self.assertTrue(
            debug_result
            and reverse_result
            and format_result
            and ssl_result
            and age
            and sort_result
        )

    def test_args_from_command_line_except_format(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=True,
            format=None,
            insecure=False,
            reverse=True,
            age=None,
            sort=None,
        )

        config = self.config["test3"]
        config_args = self.config["test3"]["arguments"]
        arguments = get_arguments(
            cli_args, config
        )
        # All arguments must contains values from cli arguments except 'format'
        # It should be from config file

        debug_result = arguments.get("debug") is True
        format_result = arguments.get("format") == config_args.get("format")
        ssl_result = arguments.get("ssl_verify") is True
        reverse_result = arguments.get("reverse") is True
        age = arguments.get('age') is None
        sort_result = arguments.get('sort') is None

        self.assertTrue(
            debug_result
            and reverse_result
            and format_result
            and ssl_result
            and age
            and sort_result
        )


    def test_args_ca_certi_invalid_path_from_config(self):
        cli_args = argparse.Namespace(
            cacert=None,
            debug=False,
            format=None,
            insecure=False,
            reverse=False,
            age=None,
        )

        config = self.config["test4"]
        with self.assertRaises(IOError) as context:
            get_arguments(
                cli_args, config
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
            age=None,
        )

        config = self.config["test5"]
        with self.assertRaises(IOError) as context:
            get_arguments(
                cli_args, config
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
            age=None,
        )
        config = self.config["test6"]
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_args, config
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
                config={}
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
                config={}
            )
            msg = "No format should be specified when selecting email output"

            self.assertTrue(msg in str(context.exception))

        cli_args = argparse.Namespace(
            format="indented", show_last_comment=0, insecure=False, cacert=None
        )
        with self.assertRaises(ValueError) as context:
            get_arguments(
                cli_arguments=cli_args,
                config={}
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
                config=config
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
                config=config
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
                config=config
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
            cli_args, config
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
                cli_args, config
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
                config={}
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
                config=config
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
                cli_args, config
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
            cli_args, config
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

    def test_age_argument_in_command_line_valid(self):

        now = datetime.datetime.now()
        expected_date = (now - relativedelta(days=5, hours=4))

        args = parse_cli_args(['--age', 'older', '5d', '4h'])

        self.assertEqual(args.age.state, 'older')
        self.assertEqual(args.age.date.replace(second=0, microsecond=0),
                         expected_date.replace(second=0, microsecond=0))

    def test_age_argument_in_config(self):

        now = datetime.datetime.now()
        expected_date = (now - relativedelta(days=5, hours=4))

        cli_args = argparse.Namespace(cacert=None, insecure=False)
        config = {
            "arguments": {
                "age": "older 5d 4h"
            }
        }

        arguments = get_arguments(
            cli_args, config
        )
        self.assertEqual(arguments.get('age').state, 'older')
        self.assertEqual(arguments.get('age').date.replace(second=0, microsecond=0),
                         expected_date.replace(second=0, microsecond=0))


    @classmethod
    def tearDownClass(cls):
        backup_filename = join(
            dirname(__file__), "test_old_format.yaml.backup"
        )
        filename = join(dirname(__file__), "test_old_format.yaml")
        if os.path.exists(filename):
            os.remove(filename)
            os.rename(backup_filename, filename)


class BaseServiceCheckRequestStateTest(unittest.TestCase):

    def test_check_request_state_newer(self):
        base_service = BaseService()
        # created four hours ago
        now = datetime.datetime.now()
        created_at = now - relativedelta(hours=4)

        # include pull request that have been added in the past day
        date = now - relativedelta(days=1)
        age = Age(date=date, state="newer")
        actual = base_service.check_request_state(created_at, age)
        self.assertTrue(actual)

        # include pull request that bave been added in the past 3 hours
        date = now - relativedelta(hours=3)
        age = Age(date=date, state="newer")
        actual = base_service.check_request_state(created_at, age)
        self.assertFalse(actual)

    def test_check_request_state_older(self):
        base_service = BaseService()
        now = datetime.datetime.now()
        # created four hours ago
        created_at = now - relativedelta(hours=4)

        # include pull request that are older than 1 day
        date = now - relativedelta(days=1)
        age = Age(date=date, state="older")
        actual = base_service.check_request_state(created_at, age)
        self.assertFalse(actual)

        # include pull request that ale older than 3 hours
        date = now - relativedelta(hours=3)
        age = Age(date=date, state="older")
        actual = base_service.check_request_state(created_at, age)
        self.assertTrue(actual)

    def test_check_request_state_age_is_none(self):
        base_service = BaseService()
        now = datetime.datetime.now()
        # created four hours ago
        created_at = now - relativedelta(hours=4)

        # No filtering
        actual = base_service.check_request_state(created_at, None)
        self.assertTrue(actual)


class ParseAgeTest(unittest.TestCase):

    def test_missing_state(self):

        with self.assertRaises(ValueError) as context:
            ParseAge.parse(['5d', '4h'])
        self.assertTrue("Wrong or missing state, only older/newer is allowed" in str(context.exception))

    def test_missing_relative_age(self):

        with self.assertRaises(ValueError) as context:
            ParseAge.parse(['newer'])
        self.assertTrue("Missing arguments" in str(context.exception))

    def test_wrong_state(self):
        with self.assertRaises(ValueError) as context:
            ParseAge.parse(['oldnew', '5d', '4h'])
        self.assertTrue("Wrong or missing state, only older/newer is allowed" in str(context.exception))

    def test_invalid_unit(self):
        with self.assertRaises(ValueError) as context:
            ParseAge.parse(['older', '5', '4x'])
        self.assertTrue("Invalid unit" in str(context.exception))


class IgnoreWIPTest(unittest.TestCase):

    def test_remove_wip(self):
        results = [
            test_mock.FakeReview(title='WIP: add a functionality'),
            test_mock.FakeReview(title='WIP:fix bug'),
            test_mock.FakeReview(title='wip:fix bug #3'),
            test_mock.FakeReview(title='wip: fix bug #4'),
            test_mock.FakeReview(title='[WIP] refactor'),
            test_mock.FakeReview(title='[WIP]refactor #2'),
            test_mock.FakeReview(title='[wip]refactor #3'),
            test_mock.FakeReview(title='[wip] refactor #4'),
            test_mock.FakeReview(
                title='[WIPER] Add the possibility of ignoring WIP PRs/MRs'
            )
        ]
        updated_results = remove_wip(results)

        # check that results with WIP in the title are removed
        self.assertEqual(len(updated_results), 1)
        self.assertEqual(
            updated_results[0].title,
            '[WIPER] Add the possibility of ignoring WIP PRs/MRs'
        )


if __name__ == "__main__":
    unittest.main()
