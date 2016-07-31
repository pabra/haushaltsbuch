SETUP
=====

```bash
sudo apt-get install python-virtualenv python3-dev
[ ! -x /bin/env ] && sudo ln -s /usr/bin/env /bin
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install -r requirements.txt
./run.py init_db
./run_local.sh
```
