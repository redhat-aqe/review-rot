import datetime
from dateutil.relativedelta import relativedelta

class BaseService(object):
    
    def __init__(self):
        pass
    
    def find_duration(self, rel_diff):
        time_list = ['year', 'month', 'day', 'hour', 'minute']
        time_dict = {'year': rel_diff.years, 'month': rel_diff.months, 'day': rel_diff.days, 'hour': rel_diff.hours, 'minute':rel_diff.minutes}
        for k,v in time_dict.items():
            if v == 0:
                if k in time_list:
                    time_list[time_list.index(k)] = ""
            elif v == 1:
                if k in time_list:
                    time_list[time_list.index(k)] = " " + str(v) + " " + k
            else:
                if k in time_list:
                    time_list[time_list.index(k)] = " " + str(v) + " " + k + "s"

        return "%s%s%s%s%s" % (time_list[0], time_list[1], time_list[2], time_list[3], time_list[4])

    def check_request_state(self, abs_diff, rel_diff, fltr, value):
        if 'y' in value:
            if fltr == 'older' and rel_diff.years < int(value.strip('y')):
                return True
            elif fltr == 'newer' and rel_diff.years > int(value.strip('y')):
                return True
        if 'm' in value:
            # find the absolute time difference in months
            abs_month = (rel_diff.years*12) + rel_diff.months
            if fltr == 'older' and abs_month < int(value.strip('m')):
                return True
            elif fltr == 'newer' and abs_month > int(value.strip('m')):
                return True
        if 'd' in value:
            if fltr == 'older' and abs_diff.days < int(value.strip('d')):
                return True
            elif fltr == 'newer' and abs_diff.days > int(value.strip('d')):
                return True
        if 'h' in value:
            # find the absolute time difference in hours
            abs_hour = (abs_diff.total_seconds)/3600
            if fltr == 'older' and diff.years < int(value.strip('h')):
                return True
            elif fltr == 'newer' and abs_hour > int(value.strip('h')):
                return True
        if 'min' in value:
            # find the absolute time difference in minutes
            abs_min = ((abs_diff.total_seconds)/60)
            if fltre == 'older' and abs_min < int(value.strip('min')):
                return True
            elif fltr == 'newer' and abs_min > int(value.strip('min')):
                return True
        return False

class BaseReviewRot(object):
    def __init__(self, user=None, title=None, url=None, time=None, comments=None):
        self.user = user
        self.title = title
        self.url = url
        self.time = time
        self.comments = comments

    def __str__(self):
        return "@%s filed '%s' %s since%s%s" % (self.user, self.title, self.url, self.time, self.comments)
