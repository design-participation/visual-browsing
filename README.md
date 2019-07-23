Visual-browsing prototype
-------------------------

This prototype allows a visual-only browsing of youtube videos. Browsing starts with an initial starting point bootstrapped with popular queries, and then iteratively allows to reach other videos by using two modes of browsing: similar videos (thanks to generic youtube recommendations), and diverse videos (random videos with seeding from popular queries).

This interface was developed with non-verbal people having intellectual disability.

To run this prototype, you need python3 as python, virtualenv, and a youtube data API key.

The Youtube key can be created at:
https://developers.google.com/youtube/v3/getting-started

It needs to be set in a file called `secrets.py` (you can use `secrets.template.py` as template).

Then, use `./run.sh` to install dependences and start the script.

