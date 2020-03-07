from functools import partial


async def run_async(loop, func, *args, **kwargs):
    """ Run a sync function in an async loop """
    return loop.run_in_executor(None, partial(func, *args, **kwargs))