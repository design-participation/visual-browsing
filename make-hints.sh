#!/bin/sh

. env/bin/activate
rm -f collections/hint_ids.json.gz

for query in $(awk '/^ *[0-9]/{print $2}' Topic\ of\ video.txt); do
  python video_collection.py collections/hint_ids.json.gz from-query $query
done
