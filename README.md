# list-pull-requests
Currently the module includes listing pull reuqests for github.

Dependencies:

Sudo pip install PyGithub

Make a config.py to store your creds. e.g,
	github = {'token': 'OAuthtoken_generated_from_github'}

Make ~/.pull-requests. e.g,
	user_name
	organization_name
	user_name/repository_name 
	organization_name/repository_name

Run:
python githubpr.py

