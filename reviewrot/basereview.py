from collections import OrderedDict
import datetime
from dateutil.relativedelta import relativedelta


class BaseService(object):

    def format_reviews(self, username, title, url, comments, created_at,
                       state_, value, duration):
        """
        find the relative time difference between now and
        review request filed to retrieve relative information
        """
        rel_diff = relativedelta(datetime.datetime.now(),
                                 created_at)
        """
        find the absolute time difference between now and
        review request filed to retrieve absolute information
        """
        abs_diff = datetime.datetime.now() - created_at
        if (state_ is not None and value is not None and
                duration is not None):
            """
            check if review request is older/newer than specified time
            interval
            """
            result = self.check_request_state(abs_diff, rel_diff,
                                              state_, value, duration)
            # skip the request if it doesn't match the specified criteria
            if not result:
                return False
        # format the time interval review request has been filed since
        time = self.format_duration(rel_diff)
        # format and print the resultant review request string
        res = {'user': username, 'title': title, 'url': url,
               'time': time, 'comments': comments}
        return res

    def format_duration(self, rel_diff):
        """
        Formats the duration the review request is pending for
        Args:
            rel_diff (relativedelta): duration the review request is pending
                                      for

        Returns:
            a string of duration the review request is pending for
        """
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

    def check_request_state(self, abs_diff, rel_diff,
                            state_, value, duration):
        """
        Checks if the review request is older or newer than specified
        time interval.
        Args:
            abs_diff (timedelta): absolute time difference between now and
                                  review request filed (used to retrieve and
                                  calculate absolute information e.g, days,
                                  hours, minutes)
            rel_diff (relativedelta): relative time difference between now and
                                  review request filed (used to retrieve and
                                  calculate absolute information e.g, month,
                                  year)
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
            abs_month = (rel_diff.years*12) + rel_diff.months
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
            abs_hour = abs_diff.total_seconds()/3600
            if state_ == 'older' and abs_hour < value:
                return False
            elif state_ == 'newer' and abs_hour >= value:
                return False
        elif duration == 'min':
            """ use abs_diff to calculate absolute time difference
            in minutes """
            abs_min = abs_diff.total_seconds()/60
            if state_ == 'older' and abs_min < value:
                return False
            elif state_ == 'newer' and abs_min >= value:
                return False
        else:
            raise ValueError("Invalid duration type: %s" % duration)
        return True


class BaseReview(object):
    def __init__(self, user=None, title=None, url=None,
                 time=None, comments=None):
        self.user = user
        self.title = title
        self.url = url
        self.time = time
        self.comments = comments

    def __str__(self):
        if(self.comments == 1):
            return ("@%s filed '%s' %s since %s with %s comment" % (
                self.user, self.title, self.url, self.time, self.comments))
        elif(self.comments > 1):
            return ("@%s filed '%s' %s since %s with %s comments" % (
                self.user, self.title, self.url, self.time, self.comments))
        else:
            return ("@%s filed '%s' %s since %s" % (self.user, self.title,
                                                    self.url, self.time))
