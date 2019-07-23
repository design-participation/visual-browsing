from aiohttp import web, ClientSession
from asyncio_compat import asyncio

import json
import shelve
import random
import atexit
import time
import string
from datetime import datetime

from youtube import Youtube
from video_collection import Collection
import action_logger as logger

SSL_CRT = 'ssl/localhost.crt'
SSL_KEY = 'ssl/localhost.key'
from secret import *

logger.setup('logs/recommended')

youtube = Youtube()

# load collections of videos
random_ids = Collection('collections/random_ids.json.gz')
target_ids_data = Collection('collections/target_ids.json.gz')
hint_ids = Collection('collections/hint_ids.json.gz')
initial_list = Collection('collections/initial_list.json.gz')

css_style = open('static/style.css').read()

def template():
    return '''<!DOCTYPE html>
    <html>
        <head>
             <meta charset="UTF-8">
            <!--<link rel="stylesheet" type="text/css" href="/static/style.css">-->
            <style>''' + css_style + '''</style>
            <script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
            <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.6.3/css/all.css" integrity="sha384-UHRtZLI+pbxtHCWp1t77Bi1L4ZtiqrqD80Kn4Z8NTSRyMA2Fd33n5dQ8lWUE00s/" crossorigin="anonymous">
        </head>
        <body>
            <div class="controls">
                <a href="javascript:history.back()"><i class="fas fa-arrow-left"></i></a>
                <a href="javascript:history.forward()"><i class="fas fa-arrow-right"></i></a>
                <a href="/"><i class="fas fa-home"></i></a>
            </div>'''

routes = web.RouteTableDef()

# simple cookie to store identity of browser
@web.middleware
async def identity_middleware(request, handler):
    if 'identity' in request.cookies:
        request.identity = request.cookies['identity']
    else:
        request.identity = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    response = await handler(request)
    response.set_cookie('identity', request.identity)
    return response

@routes.get('/video/{videoId}')
async def video(request):
    videoId = request.match_info['videoId']
    #random.seed(hash(videoId))
    logger.append('video', request.identity, videoId)
    response = web.StreamResponse()
    response.content_type = 'text/html'
    response.set_cookie('identity', request.identity) # needs to be set before sending data
    await response.prepare(request)
    await response.write(template().encode('utf8'))
    #await response.write('<center id="player"></center>\n'.encode('utf8'))
    # load video info + player
    #async def get_player():
    #    async for item in youtube.video([videoId], 50):
    #        # inject content when player get available
    #        await response.write(('<script>document.getElementById("player").innerHTML = \'%s\';</script>\n' % item['player']['embedHtml']).encode('utf8'))
    #task1 = asyncio.create_task(get_player())
    await response.write(('''<center><iframe id="ytplayer" type="text/html" width="640" height="390" src="https://www.youtube-nocookie.com/embed/''' + videoId + '''?rel=0&showinfo=0&iv_load_policy=0" frameborder="0" allow="autoplay" allowfullscreen></iframe></center>''').encode('utf8'))
    #await response.write(('''
    #    <center><iframe id="ytplayer" type="text/html" width="640" height="360"
    #      src="https://www.youtube.com/embed/''' + videoId + '''?autoplay=1"
    #      frameborder="0"></iframe></center>
    #''').encode('utf8'))

    # select random video and check that it exists
    async def get_random():
        while True:
            value = random.random()
            if value < .5:
                chosen = hint_ids.choice()
            else:
                chosen = random_ids.choice()
            if await youtube.exists(chosen):
                return chosen

    # load recommendations
    async def get_related():
        # iterator over 100 random youtube videos
        random_selection = asyncio.as_completed([asyncio.create_task(get_random()) for _ in range(100)])

        await response.write('<table id="thumbnails">\n<tr>'.encode('utf8'))
        num = 0
        async for item in youtube.related(videoId, 50):
            if num > 0 and num % 3 == 0:
                # add separator
                await response.write('<td>&nbsp;&nbsp;&nbsp;</td>'.encode('utf8'))

                # add 3 videos from the random selection
                for _ in range(3):
                    try:
                        result = await next(random_selection)
                    except StopIteration:
                        # feed more random videos as needed
                        random_selection = asyncio.as_completed([asyncio.create_task(get_random()) for _ in range(100)])
                        result = await next(random_selection)
                    await response.write(('<td class="thumbnail"><a href="/video/{id}"><img src="https://i.ytimg.com/vi/{id}/mqdefault.jpg"></a></td>'.format(id=result)).encode('utf8'))
                await response.write('</tr>\n<tr>'.encode('utf8'))
            await response.write(('<td class="thumbnail"><a href="/video/{id}"><img src="https://i.ytimg.com/vi/{id}/mqdefault.jpg"></a></td>'.format(id=item['id']['videoId'])).encode('utf8'))
            num += 1
    task2 = asyncio.create_task(get_related())

    # perform the two tasks in parallel
    #await task1
    await task2

    # trim last row
    await response.write(('</table><center style="color: gray">' + str(datetime.now()) + ' ' + request.identity + '</center>\n<script> document.querySelector("tbody tr:last-child").remove(); </script>\n').encode('utf8'))

    # load random stuff
    return response

@routes.get('/action')
async def action(request):
    async def write():
        # saving to log should not be interrupted by a dropped connection
        logger.append('action', request.identity, request.query_string)
    await asyncio.shield(write())
    return web.Response(json={'result': 'OK'})

@routes.get('/logfile/{name}')
async def logfile(request):
    filename = request.match_info['name']
    #try:
    if True:
        content = '<table border="1">'
        with open('logs/' + filename) as fp:
            lines = [line.strip().split(' ', 3) for line in fp]
            previous_session = None
            previous_timestamp = None
            for date, info, session, data in sorted(lines, key=lambda x: (x[2], x[0])):
                try:
                    timestamp = datetime.strptime(date, '%Y-%m-%d_%H:%M:%S.%f')
                except:
                    timestamp = datetime.strptime(date, '%Y-%m-%d_%H:%M:%S')
                wait = timestamp - previous_timestamp if previous_timestamp is not None else ''
                previous_timestamp = timestamp
                if previous_session != session:
                    previous_session = session
                    content += '</table><hr><table border="1">'
                if info == 'video':
                    data = '<a href="/video/{id}"><img width="256" src="https://i.ytimg.com/vi/{id}/mqdefault.jpg"></a>'.format(id=json.loads(data))
                content += '<tr><td>{session}</td><td>{date}</td><td>{wait}</td><td>{info}</td><td>{data}</td></tr>'.format(date=date, wait=wait, info=info, session=session, data=data)
    #except:
    #    raise web.HTTPNotFound(filename)
    content += '</table>'
    return web.Response(text='<DOCTYPE html><html><body>' + content + '</body></html>', content_type='text/html')

@routes.get('/logfiles')
async def logfiles(request):
    import glob
    content = '<ol>'
    for filename in sorted(glob.glob('logs/*')):
        with open(filename) as fp:
            num_lines = len(fp.readlines())
        content += '<li><a href="/logfile/{filename}">{filename}</a> ({num_lines} entries)</li>'.format(filename=filename.split('/')[-1], num_lines=num_lines)
    content += '</ol>'
    return web.Response(text='<DOCTYPE html><html><body>' + content + '</body></html>', content_type='text/html')

@routes.get('/')
async def index(request):
    #return web.HTTPFound('/video/' + random_ids.choice())
    response = web.StreamResponse()
    response.content_type = 'text/html'
    response.set_cookie('identity', request.identity) # needs to be set before sending data
    await response.prepare(request)
    await response.write(template().encode('utf8'))
    await response.write('<table>'.encode('utf8'))
    for row in range(10):
        await response.write('<tr>'.encode('utf8'))
        for item in range(6):
            videoId = initial_list[item + row * 6]
            if item == 3:
                await response.write('<td>&nbsp;&nbsp;&nbsp;</td>'.encode('utf8'))
            await response.write(('<td class="thumbnail"><a href="/video/{id}"><img src="https://i.ytimg.com/vi/{id}/mqdefault.jpg"></a></td>'.format(id=videoId)).encode('utf8'))
        await response.write('</tr>'.encode('utf8'))
    #await response.write(('</table><center style="color: gray">' + str(datetime.now()) + ' ' + request.identity + '</center>\n<script> document.querySelector("tbody tr:last-child").remove(); </script>\n').encode('utf8'))

    # load random stuff
    return response


async def init(app):
    pass

routes.static('/static', 'static', show_index=True, append_version=True)
app = web.Application(middlewares=[identity_middleware])
app.add_routes(routes) 

asyncio.get_event_loop().run_until_complete(init(app))

import ssl
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(SSL_CRT, SSL_KEY)
web.run_app(app, ssl_context=ssl_context, host=HOST, port=PORT)

