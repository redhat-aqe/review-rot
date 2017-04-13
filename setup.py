"""
from distutils.core import setup
setup(name='review-rot',
      version='0.0',
      author='Nirzari Iyer'
      author_email='niyer@redhat.com'
      description=('CLI tool to list review(pull) requests from '
                 'github,gitlab,pagure and gerrit'),
      py_modules=['reviewrot'],
      install_requires=['PyGithub', 'python-gitlab']
      )
"""
