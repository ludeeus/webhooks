"""Server handling."""
import os
from aiohttp import web

from webhooks.hacs import Hacs


ACTIVE_CLIENTS = {}

TOKEN = os.getenv("GITHUB_TOKEN")


async def hacs(request):
    """Handle POST request."""
    event_data = await request.json()
    handler = Hacs()
    handler.token = TOKEN
    await handler.initilize_hacs()
    await handler.execute(event_data)
    return web.Response(status=200)


APP = web.Application()
APP.add_routes([web.post("/hacs", hacs)])

web.run_app(APP, host="0.0.0.0")
