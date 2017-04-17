import os
import logging
import datetime
import requests
from dateutil.relativedelta import relativedelta
from base import BaseService, BaseReviewRot

log = logging.getLogger(__name__)


class PagureService(BaseService):
    def __init__(self):
        self.session = requests.session()
        self.instance = "https://pagure.io"
        self.header = None

    def request_reviews(self, user_name, repo_name=None, state_=None,
                        value=None, duration=None, host=None, token=None):
        """
        Fetches merge requests by making API calls for specified
        username(namespace) and repo(project) name.
        Formats the merge requests details and print it on console.

        Args:
            user_name (str): Pagure username or organization name
            repo_name (str): Pagure repository name for specified
                             username or organization
            state_ (str): The filter(state) for pull requests, e.g, older
                        or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month,
                            hour, minute) for requests to be older or
                            newer than
            token (str): Pagure token for authentication
                         (Commented for unauthenticated request)
            host (str): Pagure host name (Supposed to be None for project
                        scope)
        """
        # Incase authenticated pagure object is required in future
        # self.header = {"Authorization": "token " + token}
        if repo_name is not None:
            namespace = user_name
            request_url = "{}/api/0/{}/{}/pull-requests".format(self.instance,
                                                                namespace,
                                                                repo_name)
            log.debug('Looking for pull requests for %s -> %s/%s',
                      'pagure.io', namespace, repo_name)

        else:
            # absence of namespace, directly query pull requests for repo
            repo_name = user_name
            request_url = "{}/api/0/{}/pull-requests".format(self.instance,
                                                             repo_name)
            log.debug('Looking for pull requests for %s -> %s',
                      'pagure.io',  repo_name)
        log.debug('Calling API with request_url: %s', request_url)
        response = self._call_api(url=request_url)
        res_ = []
        for res in response['requests']:
            # if namespace exists in response
            try:
                repo_reference = os.path.join(res['project']['namespace'],
                                              res['project']['name'])
            except:
                repo_reference = res['project']['name']
            # format pull request url
            url = os.path.join('https://pagure.io/', repo_reference,
                               'pull-request', str(res['id']))
            # fetch the date pull request was filed at
            created_date = datetime.datetime.fromtimestamp(
                int(res['date_created'])).strftime('%Y-%m-%d %H:%M:%S')
            # format the date pull request was filed at
            try:
                date = datetime.datetime.strptime(created_date,
                                                  '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                date = datetime.datetime.strptime(created_date,
                                                  '%Y-%m-%d %H:%M:%S')
            """
            find the relative time difference between now
            and merge request filed
            """
            rel_diff = relativedelta(datetime.datetime.now(), date)
            if (state_ is not None and value is not None and
                    duration is not None):
                """
                find the absolute time difference between now
                and merge request filed
                """
                abs_diff = datetime.datetime.now() - date
                """
                check if pull request is older/newer than specified time
                interval
                """
                result = self.check_request_state(abs_diff, rel_diff,
                                                  state_=state_, value=value,
                                                  duration=duration)
                # skip the request if it doesn't match the specified criteria
                if not result:
                    log.debug("pull request '%s' is not %s than specified"
                              " time interval", res['title'], state_)
                    continue
            # format the time interval pull request has been filed since
            time = self.format_duration(rel_diff)
            # fetch and format comments for pull request
            comments = []
            if(len(res['comments']) == 1):
                comments.append('%s' % ', with 1 comment')
            elif(len(res['comments']) > 1):
                comments.append('%s %s %s' % (', with',
                                              str(len(res['comments'])),
                                              'comments'))
            comments = ' '.join(comments)
            # format and print the resultant pull request string
            res = PagureReviewRot(user=str(res['user']['name']),
                                  title=str(res['title']),
                                  url=str(url),
                                  time=time,
                                  comments=comments)
            log.info(res)
            res_.append(res)
        return res_

    def _call_api(self, url, method='GET'):
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
        req = self.session.request(
            method=method,
            url=url,
            headers=self.header,
            verify=not False,
        )
        output = None
        try:
            output = req.json()
        except Exception as err:
            log.debug('Error while decoding JSON: {0}'.format(err))
            raise Exception('Error while decoding JSON: {0}'.format(err))
        if req.status_code != 200:
            if output is None:
                log.debug('No output returned by %s', req.url)
                raise Exception('No output returned by %s' % req.url)
            if 'error_code' in output:
                log.debug(output['error'])
                raise Exception(output['error'])
        return output

    def check_request_state(self, abs_diff, rel_diff, state_, value, duration):
        return super(PagureService,
                     self).check_request_state(abs_diff, rel_diff,
                                               state_, value, duration)

    def format_duration(self, rel_diff):
        return super(PagureService, self).format_duration(rel_diff)


class PagureReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        return super(PagureReviewRot, self).__init__(*args, **kwargs)

    def __str__(self):
        return super(PagureReviewRot, self).__str__()
