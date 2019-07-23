#!/bin/sh

. env/bin/activate
rm collections/initial_list.json.gz
cat Topic\ of\ video.txt | awk '/^[ ]*[0-9]/{query=$2}/www.youtube.com/{gsub(/&.*/, "");gsub(/.*=/, "");print $1" "query}' | shuf | python video_collection.py collections/initial_list.json.gz from-txt
