import atexit
import json
import sys
from datetime import datetime

def setup(prefix):
    global fp
    fp = open(prefix + '_' + datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f') + '.txt', 'w')
    atexit.register(fp.close)

def append(name, identity, data):
    global fp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
    log_line = ' '.join([timestamp, str(name), identity, json.dumps(data)])
    print(log_line, file=sys.stderr)
    fp.write(log_line + '\n')
    fp.flush()

if __name__ == '__main__':
    import random
    setup('logs/test')
    for i in range(100):
        append(i, {'random': random.random()})
