from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

try:
    with open('requirements.txt', 'rb') as f:
        install_requires = f.read().decode('utf-8').split('\n')
except IOError:
    install_requires = []

try:
    with open('test-requirements.txt', 'rb') as f:
        tests_require = f.read().decode('utf-8').split('\n')
except IOError:
    tests_require = []

setup(name='review-rot',
      version='1.0',
      author='Maximilian Kosiarcik, Nirzari Iyer, Pavlina Bortlova,'
             ' Sid Premkumar',
      author_email='mkosiarc@redhat.com, niyer@redhat.com, '
                   'pbortlov@redhat.com, sid.premkumar@gmail.com',
      description=('CLI tool to list review(pull) requests from '
                   'gerrit, github, gitlab, pagure and phabricator'),
      long_description=long_description,
      license='GPLv3',
      url='https://github.com/redhat-aqe/review-rot',
      packages=find_packages(),
      install_requires=install_requires,
      tests_require=tests_require,
      test_suite='nose.collector',
      scripts=['bin/review-rot'],
      include_package_data=True
      )
