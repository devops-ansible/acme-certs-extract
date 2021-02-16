#!/usr/bin/env bash

apt-get -y update
apt-get install -y --no-install-recommends apt-utils
apt-get -y upgrade

pip install --upgrade pip

mkdir -p ${ACMEDIR}
mkdir -p ${CERTSDIR}

cd ${WORKDIR}
pip install -r requirements.txt

apt-get autoremove
apt-get autoclean
apt-get clean
rm -rf /var/lib/apt/lists/* /install
