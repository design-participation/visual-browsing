import sys
import json
import atexit
import random
import asyncio
import os
import gzip

from youtube import Youtube

class Collection:
    def __init__(self, filename):
        self.filename = filename
        self.changed = False
        self.db = {}
        self.load()
        atexit.register(self.save)

    def update_keys(self):
        self.keys = list(self.db.keys())

    def save(self):
        if self.changed:
            if self.filename.endswith('.gz'):
                saver = gzip.open
            else:
                saver = open
            print('saving to', self.filename, file=sys.stderr)
            with saver(self.filename, 'wb') as fp:
                fp.write(json.dumps(self.db).encode('utf8'))
            self.changed = False

    def load(self):
        if os.path.exists(self.filename):
            if self.filename.endswith('.gz'):
                loader = gzip.open
            else:
                loader = open
            print('loading from', self.filename, file=sys.stderr)
            with loader(self.filename, 'rb') as fp:
                self.db = json.loads(fp.read())
            self.update_keys()
            self.changed = False
        else:
            print('creating new collection', self.filename)

    def get(self, key):
        return self.db[key]

    def set(self, key, value):
        self.db[key] = value
        self.changed = True

    def sample(self, num):
        if self.changed:
            self.update_keys()
        return random.sample(self.keys, num)

    def choice(self):
        if self.changed:
            self.update_keys()
        return random.choice(self.keys)

    def __getitem__(self, index):
        if self.changed:
            self.update_keys()
        return self.keys[index]

    def __len__(self):
        return len(self.db)

    async def populate_random(self):
        youtube = Youtube()
        async def get_one():
            async for item in youtube.random(None, 50):
                self.db[item['id']['videoId']] = 'random'
                if len(self.db) % 100 == 0:
                    print(len(self.db))
        tasks = [get_one() for i in range(2000)]
        await asyncio.gather(*tasks)
        await youtube.close()

    async def populate_query(self, query):
        youtube = Youtube()
        async for item in youtube.search(query, 500):
            self.db[item['id']['videoId']] = query
            if len(self.db) % 100 == 0:
                print(len(self.db))
            self.changed = True
        await youtube.close()

if __name__ == '__main__':
    async def main():
        def usage():
            print('usage: %s <db-name> <from-random|from-query|size|sample|list|clear|from-txt|from-shelve> [shelve-filename]', file=sys.stderr)
            sys.exit(1)

        if len(sys.argv) == 1:
            usage()
        collection = Collection(sys.argv[1])
        if sys.argv[2] == 'from-random':
            await collection.populate_random()
        elif sys.argv[2] == 'from-query':
            await collection.populate_query(' '.join(sys.argv[3:]))
        elif sys.argv[2] == 'size':
            print(len(collection.db))
        elif sys.argv[2] == 'sample':
            for k in collection.sample(10):
                print(k)
        elif sys.argv[2] == 'list':
            for k, v in collection.db.items():
                print(k, v)
        elif sys.argv[2] == 'clear':
            with open(collection.filename, 'w') as fp:
                fp.truncate()
        elif sys.argv[2] == 'from-txt':
            for line in sys.stdin:
                k, v = line.strip().split(' ', 2)
                collection.set(k, v)
        elif sys.argv[2] == 'from-shelve':
            if len(sys.argv) != 4:
                usage()
            import shelve
            db = shelve.open(sys.argv[3])
            for k, v in db.items():
                collection.set(k, v)
            print('loaded', len(collection.db), 'items')
            db.close()
        else:
            usage()

    asyncio.get_event_loop().run_until_complete(main())


