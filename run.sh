#!/bin/bash

dir=`dirname "$0"`
cd "$dir"

if [ ! -d env ]; then
  virtualenv -p python3.7 env
  . env/bin/activate
  pip install -r requirements.txt
else
  . env/bin/activate
fi

#python youtube.py 
mkdir -p logs
python aiohttp_recommended.py 

