# review-rot
Currently the CLI tool includes listing review(pull) reuqests for github, gitlab and pagure.

## Sample I/P:
create '~/.reviewrot.yaml' with the content from sampleinput.yaml

## Installation
```shell
python setup.py install
```

Alternatively, for development:
```shell
python setup.py develop
```

## Script:

#### review-rot
```shell
> review-rot --help

usage: review-rot [-h] [-s {older,newer}] [-v VALUE] [-d {y,m,d,h,min}]
                  [--debug]

Lists pull/merge requests for github, gitlab,pagure and gerrit

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

## TODO:
-Add support for gerrit   
-Tests  
-Fix created date lag error  
