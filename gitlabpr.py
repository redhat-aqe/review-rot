import gitlab
import config

gl = gitlab.Gitlab(config.gitlab['server_host'], config.gitlab['token'])
gl.auth()
project = gl.projects.get('leanlabsio/kanban')
mrs = project.mergerequests.list(project_id=project.id,state='opened')
for mr in mrs:
    print mr.created_at
    print mr.web_url
    print mr.author.username
    print mr.user_notes_count
"""
projects = gl.projects.list()
for project in projects:
    print (project)
"""
