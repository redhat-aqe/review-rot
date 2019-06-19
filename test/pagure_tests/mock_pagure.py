"""
This file mocks some return values that are used in 'test_pagure.py'
"""


def mock_api_call_return_value():
    return {
        'requests': [
            {
                'project': {
                    'name': 'mock_repo_reference',
                    'namespace': ''
                },
                'date_created': '1',
                'last_updated': '1',
                'id': 'mock_id',
                'user': {
                    'name': 'dummy_user'
                },
                'title': 'dummy_title',
                'comments': [1, 2, 3]
            }
        ]
    }


def mock_api_call_return_value_age():
    return {
        'requests': [
            {
                'project': {
                    'name': 'mock_repo_reference',
                    'namespace': 'mock_namespace'
                },
                'date_created': '1',
                'last_updated': '1',
                'id': 'mock_id',
                'user': {
                    'name': 'dummy_user'
                },
                'title': 'dummy_title',
                'comments': [1, 2, 3]
            }
        ]
    }
