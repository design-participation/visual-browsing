from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import random
import string
import sys

import secrets
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

import asyncio
from aiohttp import ClientSession


class Youtube:
    def __init__(self):
        self.backend = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=secrets.DEVELOPER_KEY)
        self.session = ClientSession()

    async def close(self):
        await self.session.close()

    async def load(self, method, num, **parameters):
        parameters['maxResults'] = 50
        pageToken = ''
        while True:
            if 'noPageToken' not in parameters:
                parameters['pageToken'] = pageToken
            url = getattr(self.backend, method)().list(**{k: v for k, v in parameters.items() if k != 'noPageToken'}).uri
            async with self.session.get(url) as response:
                result = await response.json()
                if 'items' not in result:
                    print(url, pageToken, response.status, file=sys.stderr)
                    print(result, file=sys.stderr)
                for item in result['items']:
                    yield item
                    num -= 1
                    if num == 0:
                        return
                if 'nextPageToken' not in result or len(result['items']) == 0:
                    return
                pageToken = result['nextPageToken']

    async def search(self, query, max_results=50):
        if type(query) == list:
            query = ' '.join(query)
        async for item in self.load('search', max_results,
                q=query,
                part='id,snippet',
                type='video',
                regionCode='US',
                safeSearch='strict',
                ):
            yield item

    async def video(self, videoIds, max_results=50):
        async for item in self.load('videos', max_results,
                part='id,snippet,contentDetails,player',
                id=','.join(videoIds),
                regionCode='US',
                ):
            yield item

    async def related(self, target, max_results=50):
        async for item in self.load('search', max_results,
                part='id,snippet',
                relatedToVideoId=target,
                type='video',
                safeSearch='strict',
                videoType='movie',
                regionCode='US',
                ):
            yield item

    async def categories(self, target, max_results=50):
        async for item in self.load('videoCategories', max_results,
                part='id,snippet',
                regionCode='US',
                noPageToken=True):
            yield item

    async def popular(self, category, max_results=50):
        async for item in self.load('search', max_results,
                part='id,snippet',
                type='video',
                videoCategoryId=category,
                order='viewCount',
                regionCode='US',
                q='',
                ):
            yield item

    async def random(self, _, max_results=50):
        query = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))
        async for item in self.search(query, max_results):
            yield item

    async def exists(self, videoIds):
        async def test_existence(videoId):
            url = 'https://i.ytimg.com/vi/%s/default.jpg' % videoId
            async with self.session.head(url) as request:
                await request.text()
                return request.status == 200
        if type(videoIds) == str:
            return await test_existence(videoIds)
        else:
            return await asyncio.gather(*[asyncio.create_task(test_existence(videoId)) for videoId in videoIds])


if __name__ == '__main__':
    async def main(loop):
        import sys
        if len(sys.argv) < 2:
            print('usage: %s <search|related|video|categories|popular|random|exists> <query|id|category>' % sys.argv[0])
            sys.exit(1)

        youtube = Youtube()
        method = sys.argv[1]
        if method in ['search', 'related', 'video', 'categories', 'popular', 'random']:
            async for item in getattr(youtube, method)(sys.argv[2:], -1):
                print(json.dumps(item, indent=4, sort_keys=True))
        elif method == 'exists':
            print(await youtube.exists(sys.argv[2:]))
        else:
            print('ERROR: unknown method "%s"' % method)
        await youtube.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

