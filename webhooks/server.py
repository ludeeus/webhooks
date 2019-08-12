"""Server handling."""
# app logic from: https://github.com/Mariatta/gh_app_demo
import jwt
import time
from aiohttp import web, ClientSession


from webhooks.hacs import Hacs


def get_jwt(app_id):
    pem_file = open("/cert/hacsbot.pem", "rt").read()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": app_id,
    }
    encoded = jwt.encode(payload, pem_file, algorithm="RS256")
    bearer_token = encoded.decode("utf-8")

    return bearer_token


async def hacs(request):
    """Handle POST request."""
    event_data = await request.json()
    if event_data.get("comment") is not None:
        if event_data["comment"]["user"]["type"] == "Bot":
            # Skip bots
            return web.Response(status=200)
        elif event_data["comment"]["user"]["login"] == "ludeeus":
            # Skip ludeeus
            return web.Response(status=200)
    jwtoken = get_jwt(38284)
    async with ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {jwtoken}",
            "Accept": "application/vnd.github.machine-man-preview+json",
        }
        token = await session.post(
            "https://api.github.com/app/installations/1473269/access_tokens",
            headers=headers,
        )
        token = await token.json()
        token = token["token"]
        handler = Hacs(session)
        handler.token = token
        await handler.initilize_hacs()
        await handler.execute(event_data)
    return web.Response(status=200)


APP = web.Application()
APP.add_routes([web.post("/hacs", hacs)])

web.run_app(APP, host="0.0.0.0")
