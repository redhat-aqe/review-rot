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
      author='Nirzari Iyer, Sid Premkumar, Pavlina Bortlova,'
             ' Maximilian Kosiarcik',
      author_email='niyer@redhat.com, sid.premkumar@gmail.com, '
                   'pbortlov@redhat.com, mkosiarc@redhat.com',
      description=('CLI tool to list review(pull) requests from '
                   'github, gitlab and pagure'),
      long_description=long_description,
      license='GPLv3',
      url='https://github.com/nirzari/review-rot',
      packages=find_packages(),
      install_requires=install_requires,
      tests_require=tests_require,
      test_suite='nose.collector',
      scripts=['bin/review-rot'],
      include_package_data=True
      )
