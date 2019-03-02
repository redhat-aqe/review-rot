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

usage: review-rot [-h] [-c CONFIG] [-s {older,newer}] [-v VALUE]
                  [-d {y,m,d,h,min}] [-f {oneline,indented,json}]
                  [--show-last-comment [DAYS]] [--reverse]
                  [--sort {submitted, updated, commented}] [--debug]
                  [--email EMAIL [EMAIL ...]] [--irc CHANNEL [CHANNEL ...]]
                  [-k] [--cacert CACERT]

Lists pull/merge/change requests for github, gitlab, pagure and gerrit

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file to use
  -s {older,newer}, --state {older,newer}
                        Pull requests state 'older' or 'newer'
  -v VALUE, --value VALUE
                        Pull requests duration in terms of value(int)
  -d {y,m,d,h,min}, --duration {y,m,d,h,min}
                        Pull requests duration in terms of y=years,m=months,
                        d=days, h=hours, min=minutes
  -f {oneline,indented,json}, --format {oneline,indented,json}
                        Choose from one of a few different styles
  --show-last-comment [DAYS]
                        Show text of last comment and filter out pull requests
                        in which last comments are newer than specified number
                        of days
  --reverse             Display results with the most recent first
  --sort {submitted,updated,commented}
                        Display results sorted by the chosen event time.
                        Defaults to submitted
  --debug               Display debug logs on console
  --email EMAIL [EMAIL ...]
                        send output to list of email adresses
  --irc CHANNEL [CHANNEL ...]
                        send output to list of irc channels

SSL:
  -k, --insecure        Disable SSL certificate verification (not recommended)
  --cacert CACERT       Path to CA certificate to use for SSL certificate
                        verification

```

You can use **--show-last-comment** flag to include the text of last comment with formats:
- json
```
review-rot -f json --show-last-comment
```
- email
```
review-rot --email user@example.com --show-last-comment
```

## Web UI

There is a static html+js web interface that can read in the output of the
`review-rot` CLI tool and produce a web page:

First, set up a *cron job* to run review-rot every (say) 15 minutes:

```shell
*/15 * * * * review-rot -f json > /home/someuser/public_html/reviewrot/data.json
```

Then, modify `web/js/site.js` to point the data url to the location of your new file.

## Email notification

To use email notification functionality you must specify mailer configuration in config file
```
mailer:
  sender: do-not-reply@example.com
  server: smtp.example.com
```

then specify email addresses in config file:
```
arguments:
  email: user1@example.com, user2@example.com
```

Or in command line:
```
review-rot --email user1@example.com user2@example.com
```

## IRC notification

To use irc notification functionality you must specify irc server configuration in config file
```
irc:
  server: irc.example.com
  port: 12345
```

then specify channels in config file for example:
```
arguments:
  # don't forget to use quotes
  irc: '#channel1, #channel2'
```

Or in command line:
```
# don't forget to use quotes or backslash
review-rot --irc '#channel1' '#channel2'
review-rot --irc \#channel1 \#channel2
```
