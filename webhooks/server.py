"""Server handling."""
import os
from aiohttp import web

from webhooks.hacs import Hacs


ACTIVE_CLIENTS = {}

TOKEN = os.getenv("GITHUB_TOKEN")


async def hacs(request):
    """Handle POST request."""
    handler = Hacs()
    handler.token = TOKEN
    await handler.initilize_hacs()

    event_data = await request.json()
    if "pull_request" in event_data:
        issue_number = event_data["number"]
        submitter = event_data["pullrequest"]["user"]["login"]
        await handler.handle_greeting(issue_number, submitter)
        if event_data["pull_request"]["base"]["ref"] == "data":
            await handler.handle_new_repo_pr_data(event_data)
    return web.Response(status=200)


APP = web.Application()
APP.add_routes([web.post("/hacs", hacs)])

web.run_app(APP, host="0.0.0.0")
