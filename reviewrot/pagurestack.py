import os
import logging
import datetime
import requests
from reviewrot.basereview import BaseService, BaseReview

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
            host (str): Pagure host name (This value is not yet supported.
                        The default behavior is to use public pagure instance)
        Returns:
            res_ (list): Returns list of pull requests for specified
                         namespace and/or repo name
        """
        # Authenticated pagure object can be uncommented for future use
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
            """ check if review request is older/newer than specified time
            interval"""
            result = self.check_request_state(date,
                                              state_, value, duration)
            if result is False:
                log.debug("pull request '%s' is not %s than specified"
                          " time interval", res['title'], state_)
                continue
            # format the time interval pull request has been filed since
            time = self.format_duration(created_at=date)
            res = PagureReview(user=res['user']['name'],
                               title=res['title'],
                               url=url,
                               time=time,
                               comments=len(res['comments']))
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
        )
        output = None
        try:
            output = req.json()
        except Exception as err:
            log.exception('Error while decoding JSON: {0}'.format(err))
            raise
        if req.status_code != 200:
            if 'error_code' in output:
                log.debug(output['error'])
                raise Exception(output['error'])
        return output


class PagureReview(BaseReview):
    pass
