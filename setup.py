from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

setup(name='review-rot',
      version='0.0',
      author='Nirzari Iyer',
      author_email='niyer@redhat.com',
      description=('CLI tool to list review(pull) requests from '
                   'github, gitlab and pagure'),
      long_description=long_description,
      license='GPLv3',
      url='https://github.com/nirzari/review-rot',
      packages=find_packages(),
      install_requires=[
          'requests>=2.14.0',
          'PyGithub',
          'PyYAML',
          'dateutils',
          'python-gitlab==1.5.1',
      ],
      tests_require=[
          'nose',
          'mock',
      ],
      test_suite='nose.collector',
      scripts=['bin/review-rot']
      )
