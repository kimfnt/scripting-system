#!/bin/bash

# we verify the python3 version on the linux distribution
python3 --version

# upgrade to the latest version
sudo apt-get install --upgrade python3

# install pip
sudo apt-get install python3-pip

# check installation has succeeded
python3 -m pip --version

# install the dependencies used in the project
python3 -m pip install email-validator
python3 -m pip install pysmb

# create crontab to automatise the process
# By default, the service will be launched daily at 12:00PM
{
  crontab -l -u $USER;
  echo "00 12 * * * cd $PWD; python3 main.py";

} | crontab -u $USER -

# verify crontab was created
if sudo test -f "/var/spool/cron/crontabs/$USER"
then
  echo "Crontab created in /var/spool/cron/crontabs"
  sudo service cron start
else
  echo "ERROR: crontab not created"
fi