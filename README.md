review-rot

# list-pull-requests
Currently the tool includes listing pull reuqests for github and gitlab.

Sample I/P:
create '~/.pull-requests.yaml' with the content from sampleinput.yaml

Dependencies:

Sudo pip install PyGithub
pip install --upgrade python-gitlab

Run:
python reviewrot.py

TODO:
-Error handling
-Setup.py
-Logging
-Pagure.io, gerrit
-Tests
