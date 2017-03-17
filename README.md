# list-pull-requests
Currently the module includes listing pull reuqests for github.

Dependencies:

Sudo pip install PyGithub

Write a config.py having to store your creds. e.g,
	github = {'uname': 'username', 'pwd': 'python'}
Make ~/.pull-requests. e.g,
	user_name
	organization_name
	user_name/repository_name 
	organization_name/repository_name

Run:
python githubpr.py

