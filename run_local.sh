#!/bin/bash

BIN_READLINK=$( test -f /usr/local/bin/greadlink && echo "greadlink" || echo "readlink" )
DIR="$( dirname "$( $BIN_READLINK -f "$0" )" )"

cd ${DIR}
XDG_OPEN=$( which xdg-open )

source ${DIR}/venv/bin/activate

URL=$( ${DIR}/run.py get_url )

[ "$XDG_OPEN" ] && sleep 0.5 && $XDG_OPEN $URL >/dev/null 2>&1 &

${DIR}/run.py
