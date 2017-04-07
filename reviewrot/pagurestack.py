import yaml
import logging
import datetime
import requests
from dateutil.relativedelta import relativedelta
from base import BaseService, BaseReviewRot
from os.path import expanduser

class PagureService(BaseService):
    def __init__(self):
        home = expanduser('~')
        with open(home + '/.config.yaml', 'r') as f:
            config = yaml.load(f)
        #self.token = config['creds']['pagure']['token']
        #self.header = {"Authorization": "token " + pagure_token}
        self.log = logging.getLogger(__name__)
        self.session = requests.session()
        self.instance="https://pagure.io"
        #self.header = {"Authorization": "token " + pagure_token}
        self.header = None

    
    def request_reviews(self, user_name, repo_name=None, fltr=None, value=None):
        if repo_name is not None:
            namespace = user_name
            request_url = "{}/api/0/{}/{}/pull-requests".format(self.instance, namespace, repo_name)

        else:
            # absence of namespace, directly query pull requests for repo
            repo_name = user_name
            request_url = "{}/api/0/{}/pull-requests".format(self.instance, repo_name)
        
        response = self._call_api(url=request_url)
        for res in response['requests']:
            try:
                repo_reference = res['project']['namespace'] + '/' + res['project']['name']
            except:
                repo_reference = res['project']['name']
            url = 'https://pagure.io/' + repo_reference + '/pull-request/' + str(res['id'])
            created_date = datetime.datetime.fromtimestamp(int(res['date_created'])).strftime('%Y-%m-%d %H:%M:%S')
            try:
                    date = datetime.datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                    date = datetime.datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
            # find the relative time difference between now and merge request filed
            rel_diff = relativedelta(datetime.datetime.now(), date)
            if fltr is not None and value is not None:
                # find the absolute time difference between now and merge request filed
                abs_diff = datetime.datetime.now() - date
                # check for older/newer requests
                result = self.check_request_state(abs_diff, rel_diff, fltr, value)
                if result == True:
                    continue
            # format time
            time = self.find_duration(rel_diff)
            if(len(res['comments']) == 0):
                comments = ""
            elif(len(res['comments']) == 1):
                comments = ", with 1 comment"
            else:
                comments = ", with  " + str(len(res['comments'])) + " comments "
            res = PagureReviewRot(user=str(res['user']['name']), title=str(res['title']), url=str(url), time=time, comments=comments)
            print res

    def _call_api(self, url, method='GET'):
        """ Method used to call the API.
        It returns the raw JSON returned by the API or raises an exception
        if something goes wrong.
        :arg url: the URL to call
        :kwarg method: the HTTP method to use when calling the specified
            URL, can be GET, POST, DELETE, UPDATE...
            Defaults to GET
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
            # TODO: Log it
            raise Exception('Error while decoding JSON: {0}'.format(err))
        if req.status_code != 200:
            #TODO: Log it
            if output is None:
                raise Exception(
                    'No output returned by %s' % req.url)
            if 'error_code' in output:
                print ("Invalid request")
        return output
    
    def check_request_state(self, abs_diff, rel_diff, fltr, value):
        return super(PagureService, self).check_request_state(abs_diff, rel_diff, fltr, value)

    def find_duration(self, rel_diff):
        return super(PagureService, self).find_duration(rel_diff)

class PagureReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        return super(PagureReviewRot, self).__init__(*args, **kwargs)

    def __str__(self):
        return super(PagureReviewRot, self).__str__()
