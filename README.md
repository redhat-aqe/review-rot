# review-rot
reviewrot is a CLI tool, that helps to list down open review requests from github, gitlab, pagure and gerrit.

## Sample I/P:
Create '~/.reviewrot.yaml'. browse the [examples](https://github.com/nirzari/review-rot/tree/master/examples/) for content. 

## Installation
```shell
python setup.py install
```

Alternatively, for development:
```shell
python setup.py develop
```

## Tests
To run the tests in your virtualenv, execute:
```shell
python setup.py test
```

Alternatively, you can use `tox` or `detox` to run the tests against multiple versions of python:
```shell
sudo dnf install python-detox
detox
```

## Script:

#### review-rot
```shell
> review-rot --help

usage: review-rot [-h] [-s {older,newer}] [-v VALUE] [-d {y,m,d,h,min}]
                  [--debug]

Lists pull/merge/change requests for github, gitlab, pagure and gerrit

optional arguments:
  -h, --help            show this help message and exit
  -s {older,newer}, --state {older,newer}
                        Pull requests state 'older' or 'newer'
  -v VALUE, --value VALUE
                        Pull requests duration in terms of value(int)
  -d {y,m,d,h,min}, --duration {y,m,d,h,min}
                        Pull requests duration in terms of y=years,m=months,
                        d=days, h=hours, min=minutes
  --debug               Display debug logs on console
```

## Web UI

There is a static html+js web interface that can read in the output of the
`review-rot` CLI tool and produce a web page:

First, set up a *cron job* to run review-rot every (say) 15 minutes:

```shell
*/15 * * * * review-rot -f json > /home/someuser/public_html/reviewrot/data.json
```

Then, modify `web/js/site.js` to point the data url to the location of your new file.
