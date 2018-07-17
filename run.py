import copy
import os
import time

import gdapi
from japronto import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler

client = None
if 'CATTLE_ACCESS_KEY' in os.environ and 'CATTLE_SECRET_KEY' in os.environ:
    client = gdapi.Client(url=os.environ['CATTLE_URL'].replace('v1', 'v2-beta'),
                          access_key=os.environ['CATTLE_ACCESS_KEY'],
                          secret_key=os.environ['CATTLE_SECRET_KEY'])
else:
    client = gdapi.Client(url=os.environ['CATTLE_URL'].replace('v1', 'v2-beta'))

STACKS = {}
PROJECTS = None
OLD_CONTAINERS = []
STAY_TIME = float(int(os.getenv('STAY_TIME', 7)) * 86400)
STAY_TIME_STACK = float(int(os.getenv('STAY_TIME_STACK', 1)) * 86400)
CLEANUP_STACKS = os.getenv('CLEANUP_STACKS', '').split(',')
CLEANUP_SERVICE_IN_STACKS = os.getenv('CLEANUP_SERVICE_IN_STACKS', '').split(',')


async def index(request):
    return request.Response(json=[])


async def get_project_and_stacks():
    global STACKS
    global PROJECTS
    global client
    PROJECTS = client.by_id_project(os.environ['ENVIRONMENT'])
    STACKS = {i.name: i for i in PROJECTS.stacks()}


async def find_old_containers():
    global PROJECTS
    global OLD_CONTAINERS
    paginate = 0
    containers = []
    this_time = time.time() - STAY_TIME
    while True:
        data = PROJECTS.containers(marker=f'm{paginate}').data
        if not data:
            break
        containers += filter(lambda
                                 x: x.labels.get('io.rancher.stack_service.name') is not None
                                    and x.labels.get('io.rancher.container.system') is None
                                    and this_time > (x.createdTS / 1000),
                             data)
        paginate += 100
    OLD_CONTAINERS = containers


async def clean_old_ss():
    global OLD_CONTAINERS
    global STACKS
    global CLEANUP_STACKS
    global CLEANUP_SERVICE_IN_STACKS
    stack_to_remove = []
    service_to_remove = []
    this_time = time.time() - STAY_TIME
    containers = copy.copy(OLD_CONTAINERS)
    for container in containers:
        data = container.labels.get('io.rancher.stack_service.name').split('/')
        stack, service = data[0], data[1]
        try:
            for cleanup in CLEANUP_STACKS:
                if stack not in STACKS.keys():
                    continue
                if STACKS[stack].description is None:
                    continue
                if stack.startswith(cleanup) \
                        and this_time > (container.createdTS / 1000) \
                        and not STACKS[stack].description.lower().startswith('need') \
                        and STACKS[stack] not in stack_to_remove:
                    stack_to_remove.append(STACKS[stack])
        except Exception as e:
            print(e)
        try:
            if stack in CLEANUP_SERVICE_IN_STACKS \
                    and not service.startswith('develop') \
                    and not service.startswith('master') \
                    and not service.startswith('release'):
                for i in container.services().data:
                    if i not in service_to_remove:
                        service_to_remove.append(i)
        except Exception as e:
            print(e)
    try:
        for stack in stack_to_remove:
            print(f"remove {stack.name}")
            stack.remove()
        for service in service_to_remove:
            print(f"remove {service.stack().name}/{service.name}")
            service.remove()
    except Exception as e:
        print(e)

async def connect_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(get_project_and_stacks, 'interval', seconds=int(os.getenv('get_project_and_stacks', 1800)))
    scheduler.add_job(find_old_containers, 'interval', seconds=int(os.getenv('find_old_containers', 1200)))
    scheduler.add_job(clean_old_ss, 'interval', seconds=int(os.getenv('remove_old_ss', 600)))
    scheduler.start()


app = Application()
app.loop.run_until_complete(get_project_and_stacks())
app.loop.run_until_complete(find_old_containers())
app.loop.run_until_complete(clean_old_ss())
app.loop.run_until_complete(connect_scheduler())
router = app.router
router.add_route('/', index)
app.run(debug=bool(int(os.getenv('DEBUG', 0))))
