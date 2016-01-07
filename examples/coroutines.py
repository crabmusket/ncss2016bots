import asyncio

@asyncio.coroutine
def interruptible(name):
    print(name, 'Starting!')
    yield
    print(name, 'One yield down')
    x = yield
    print(name, 'was sent', x)
    yield
    print(name, 'Done!')

def run_until_done(coroutine):
    coroutine.send(None)
    while True:
        try:
            coroutine.send('hi')
        except StopIteration:
            print('it stopped')
            break
