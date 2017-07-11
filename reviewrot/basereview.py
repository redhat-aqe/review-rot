import datetime
import json
import logging
import time

from collections import OrderedDict

from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)


class BaseService(object):
    def check_request_state(self, created_at,
                            state_, value, duration):
        """
        Checks if the review request is older or newer than specified
        time interval.
        Args:
            created_at (str): the date review request was filed
            state_ (str): state for review requests, e.g, older
                          or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month, hour
                            minute) for requests to be older or newer than

        Returns:
            True if the review request is older or newer than
            specified time interval, False otherwise
        """
        if state_ is not None and value is not None\
                and duration is not None:
            """
            find the relative time difference between now and
            review request filed to retrieve relative information
            """
            rel_diff = relativedelta(datetime.datetime.utcnow(),
                                     created_at)
            """
            find the absolute time difference between now and
            review request filed to retrieve absolute information
            """
            abs_diff = datetime.datetime.utcnow() - created_at

            if state_ not in ('older', 'newer'):
                raise ValueError('Invalid state value: %s' % state_)
            if duration == 'y':
                """ use rel_diff to retrieve absolute year since
                value of absolute and relative year is same."""
                if state_ == 'older' and rel_diff.years < value:
                    return False
                elif state_ == 'newer' and rel_diff.years >= value:
                    return False
            elif duration == 'm':
                """ use rel_diff to calculate absolute time difference
                in months """
                abs_month = (rel_diff.years * 12) + rel_diff.months
                if state_ == 'older' and abs_month < value:
                    return False
                elif state_ == 'newer' and abs_month >= value:
                    return False
            elif duration == 'd':
                """ use abs_diff to retrieve absolute time difference
                in days """
                if state_ == 'older' and abs_diff.days < value:
                    return False
                elif state_ == 'newer' and abs_diff.days >= value:
                    return False
            elif duration == 'h':
                """ use abs_diff to calculate absolute time difference
                in hours """
                abs_hour = abs_diff.total_seconds() / 3600
                if state_ == 'older' and abs_hour < value:
                    return False
                elif state_ == 'newer' and abs_hour >= value:
                    return False
            elif duration == 'min':
                """ use abs_diff to calculate absolute time difference
                in minutes """
                abs_min = abs_diff.total_seconds() / 60
                if state_ == 'older' and abs_min < value:
                    return False
                elif state_ == 'newer' and abs_min >= value:
                    return False
            else:
                raise ValueError("Invalid duration type: %s" % duration)
        return True

    def _decode_response(self, response):
        """
        Remove Gerrit's prefix and convert to JSON.
        Args:
            response (Response): Content is decoded from response object
        Returns:
            Converted JSON content
        Raises:
            ValueError if the content is not in proper json format.
        """
        gerrit_json_prefix = ")]}\'\n"
        content = response.content.strip()
        try:
            if response.encoding:
                content = content.decode(response.encoding)
            if content.startswith(gerrit_json_prefix):
                content = content[len(gerrit_json_prefix):]
            return json.loads(content)
        except ValueError:
            raise ValueError('Invalid json content: %s' % content)

    def _call_api(self, url, method='GET', ssl_verify=True, ignore_err=False):
        """
        Method used to call the API.
        It returns the raw JSON returned by the API or raises an exception
        if something goes wrong.
        Args:
            method (str): the URL to call, can be GET, POST, DELETE, UPDATE...
                          Defaults to GET
        Returns:
            raw JSON returned by API
        """
        decoded_response = ''
        try:
            response = self.get_response(method, url, ssl_verify)
            decoded_response = response.json()
            # Some services (like pagure) return valid JSON with a 404 error.
            # https://pagure.io/api/0/username/reponame/pull-requests
            if not response:
                raise ValueError("%r gave %r: %r" % (
                    response.request, response, decoded_response))
        except ValueError:
            if response.status_code == 404:
                # happens when comments are not found for Gerrit Change Request
                if not ignore_err:
                    raise ValueError('Page not found: %s' % response.url)
            elif response.status_code == 200:
                try:
                    decoded_response = self._decode_response(response)
                except Exception as e:
                    raise ValueError('Error while decoding JSON:{0}'.format(e))
            else:
                raise
        return decoded_response

    def get_response(self, method, url, ssl_verify):
        return self.session.request(method=method, url=url,
                                    headers=self.header, verify=ssl_verify)


class BaseReview(object):
    def __init__(self, user=None, title=None, url=None,
                 time=None, comments=None, image=None):
        self.user = user
        self.title = title
        self.url = url
        self.time = time
        self.comments = comments
        self.image = image

    @staticmethod
    def format_duration(created_at):
        """
        Formats the duration the review request is pending for
        Args:
            created_at (str): the date review request was filed

        Returns:
            a string of duration the review request is pending for
        """
        """
        find the relative time difference between now and
        review request filed to retrieve relative information
        """
        rel_diff = relativedelta(datetime.datetime.utcnow(),
                                 created_at)

        time_dict = OrderedDict([
            ('year', rel_diff.years),
            ('month', rel_diff.months),
            ('day', rel_diff.days),
            ('hour', rel_diff.hours),
            ('minute', rel_diff.minutes),
        ])

        result = []
        for k, v in time_dict.items():
            if v == 1:
                result.append('%s %s' % (v, k))
            elif v > 1:
                result.append('%s %ss' % (v, k))

        return ' '.join(result)

    @property
    def since(self):
        return self.format_duration(created_at=self.time)

    def __str__(self):
        return self.format('oneline')

    def format(self, style, i, N):
        """ Format the result in a given style.

        style - the name of the style.
        i - an integer, indicating the position in a list.
        N - the total size of the list.
        """
        lookup = {
            'oneline': self._format_oneline,
            'indented': self._format_indented,
            'json': self._format_json,
        }
        return lookup[style](i, N)

    def _format_oneline(self, i, N):
        string = "@%s filed '%s' %s since %s" % (
            self.user, self.title, self.url, self.since)

        if self.comments == 1:
            string += " with %s comment" % self.comments
        elif self.comments > 1:
            string += " with %s comments" % self.comments

        return string

    def _format_indented(self, i, N):
        string = "@%s filed '%s'\n\t%s\n\tsince %s" % (
            self.user, self.title, self.url, self.since)

        if self.comments == 1:
            string += "\n\twith %s comment" % self.comments
        elif self.comments > 1:
            string += "\n\twith %s comments" % self.comments

        return string

    def _format_json(self, i, N):
        import json
        # Include a comma after every entry, except the last.
        suffix = ',' if i < N - 1 else ''
        return json.dumps(self.__json__(), indent=2) + suffix

    def __json__(self):
        return {
            'user': self.user,
            'title': self.title,
            'url': self.url,
            'relative_time': self.since,
            'time': time.mktime(self.time.timetuple()),
            'comments': self.comments,
            'type': type(self).__name__,
            'image': self.image,
        }