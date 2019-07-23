import asyncio

if not hasattr(asyncio, 'create_task'):
    asyncio.create_task = asyncio.ensure_future
