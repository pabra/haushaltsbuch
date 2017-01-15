INFO
====

A simple tool to track your expenses. This might be the next evolutionary step after
a spreadsheet for this purpose and before using a more complex tool that wants
access to you bank account.

The intend of this tool is to run just on the localhost of your machine. You could
run it on a server too but than you should think about authentication, encryption, etc.

It runs in a Python virtual environment, serves on top of Flask and stores your
data in a SQLite database. The user interface runs entirely in your browser using
jQuery, jQuery UI and Knockout.


SETUP
=====

```bash
# clone the repository
git clone https://github.com/pabra/haushaltsbuch.git
cd haushaltsbuch
# get virtualenv for Ubuntu - for other distributions search for `virtualenv` in the repository
sudo apt-get install python-virtualenv python3-dev
# have `env` at an expected place
[ ! -x /bin/env ] && sudo ln -s /usr/bin/env /bin
# set up a virtual environment in `venv` directory and activate it
virtualenv -p $(which python3) venv
source venv/bin/activate
# install requirements in this virtual environment
pip install -r requirements.txt
# copy the config template and edit for your needs
cp config.template.py config.py
vim config.py
# initialiize the database
# !!! this will overwrite the data that's currently in your database !!!
./run.py init_db
```


RUN
===

```bash
./run_local.sh
```
