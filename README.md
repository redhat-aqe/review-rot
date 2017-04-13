# review-rot

Currently the CLI tool includes listing pull reuqests for github, gitlab and pagure.

### Sample I/P:
create '~/.reviewrot.yaml' with the content from sampleinput.yaml

### Dependencies:

Sudo pip install PyGithub  
pip install --upgrade python-gitlab

### Run:
python reviewrot.py

optional arguments:  
  -h, --help			show this help message and exit  
  -s {older,newer}, --state {older,newer}  
					Pull requests state 'older' or 'newer'  
  -v VALUE, --value VALUE  
					Pull requests duration in terms of value(int)  
  -d {y,m,d,h,min}, --duration {y,m,d,h,min}  
					Pull requests duration in terms of y=years,m=months,  
					d=days, h=hours, min=minutes  

### TODO:
-Change logging location if required
-Setup.py  
-Add support for gerrit   
-Tests  
-Fix created date lag error
