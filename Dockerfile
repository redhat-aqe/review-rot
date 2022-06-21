FROM registry.access.redhat.com/ubi8/ubi-minimal
MAINTAINER Pavlina Bortlova <pbortlov@redhat.com>

LABEL \
    description="Review-rot - gather information about opened merge or pull requests" \
    summary="review-rot git gitlab github pagure gerrit" \
    vendor="EXD Process-tools guild <exd-guild-process-tools@redhat.com>"

USER root

RUN microdnf update \
    && microdnf install \
        gcc \
        git \
        libyaml-devel \
        python39-devel \
        python39-pip \
        python39-setuptools \
    && microdnf clean all

# copy workdir for installation of review-rot
COPY . /reviewrot

# install review-rot
RUN cd /reviewrot \
    && pip3 install --upgrade pip setuptools \
    && python3 setup.py install

# clean up and remove no longer needed dependencies for building Python
# packages
RUN rm -r /reviewrot \
    && microdnf remove \
        gcc \
        libyaml-devel \
        python3-devel \
    && microdnf clean all

# create direcory for the run of review-rot,
# set privileges and env variable
RUN mkdir -p /.cache/Python-Eggs \
    && chmod g+rw /.cache/Python-Eggs
ENV PYTHON_EGG_CACHE=/.cache/Python-Eggs
