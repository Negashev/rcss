import os

import gdapi
from japronto import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler

if 'CATTLE_ACCESS_KEY' in os.environ and 'CATTLE_SECRET_KEY' in os.environ:
    client = gdapi.Client(url=os.environ['CATTLE_URL'].replace('v1', 'v2-beta'),
                          access_key=os.environ['CATTLE_ACCESS_KEY'],
                          secret_key=os.environ['CATTLE_SECRET_KEY'])
else:
    client = gdapi.Client(url=os.environ['CATTLE_URL'].replace('v1', 'v2-beta'))

STACK = None

async def index(request):
    return request.Response(json=[])


async def get_stacks():
    global STACK
    project = client.by_id_project(os.environ['ENVIRONMENT'])
    STACK = project.list_stacks()


async def connect_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    # scheduler.add_job(p1, 'interval', seconds=1)

    scheduler.start()


app = Application()
app.loop.run_until_complete(get_stacks())
app.loop.run_until_complete(connect_scheduler())
router = app.router
router.add_route('/', index)
app.run(debug=bool(int(os.getenv('DEBUG', 0))))
