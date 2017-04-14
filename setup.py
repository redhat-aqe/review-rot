from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

setup(name='review-rot',
      version='0.0',
      author='Nirzari Iyer',
      author_email='niyer@redhat.com',
      description=('CLI tool to list review(pull) requests from '
                   'github,gitlab,pagure and gerrit'),
      long_description=long_description,
      license='Apache License 2.0',
      url='https://github.com/nirzari/review-rot',
      packages=find_packages(),
      install_requires=['PyGithub', 'python-gitlab', 'mock'],
      scripts=['bin/review-rot']
      )
