import uvicorn

import bleach  # for cleaning HTML

import sys

from random import random
import requests
from datetime import timedelta, datetime
import asyncio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount('/static', StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index3.html", {"request": request})

# websocket and state handling
all_connections = []

LIST_RESOURCES = r"../resources/list_items"
GRID_RESOURCES = r"../resources/grid_state"
NOTE_RESOURCES = r"../resources/notices"

# format of a tuple: (ITEMNAME, ITEMID)
# i am loading these into array, because like
# i dont wanna deal with that much disk IO
all_items: list[tuple] = []

# grid format: [STATE_1, STATE_2, STATE_3, STATE_4] for each weekday
# STATES = E, X, ?, O
grid: list[list[str]] = []
notices: list[str] = []
global item_count
item_count = 0

# load the initially saved items
with open(LIST_RESOURCES, "r") as itemsFile:
    raw_items = itemsFile.readlines()
    for raw in raw_items:
        t = raw.replace('\n', "")

        if t == "":
            continue

        t = t.split("^")
        print(t)
        item_id = int(t[1])
        if item_id >= item_count:
            item_count = item_id + 1
        all_items.append((t[0], item_id))

with open(GRID_RESOURCES, "r") as gridFile:
    raw_grid = gridFile.readlines()

    for raw in raw_grid:
        tRaw = raw.replace("\n", "")
        grid.append(tRaw.split(","))

    print("Finished Grid:", grid)


with open(NOTE_RESOURCES, "r") as noticesFile:
    raw_notices = noticesFile.readlines()

    # TODO, yes this is a bit primitive, I was too lazy to attach IDs
    for raw in raw_notices:
        tRaw = raw.replace("\n", "")
        notices.append(tRaw)

    print("Finished Notices:", notices)

outer_grid_map = ["monday", "tuesday", "wednesday",
                  "thursday", "friday", "saturday", "sunday"]

inner_grid_map = ["rick", "youri", "robert", "milan"]


@app.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    all_connections.append(websocket)
    global item_count
    global notices

    try:
        while True:
            data = await websocket.receive_text()
            data = bleach.clean(data)
            print(f"/========/ passed: {data} /========/")

            """
            Data has the following format now
            [event]^[mEffectedItem]^[mNewValue]
            """
            # formatting the data
            data = data.split("^")
            event = data[0]
            mEffectedItem = data[1]
            mNewValue = data[2]

            if event == "addItem":
                all_items.append((mNewValue, item_count))
                await broadcast_to_sockets(f"{event}^{item_count}^{mNewValue}")
                item_count += 1

            elif event == "deleteItem":
                mTempId = mEffectedItem.split("-")[1]
                all_items.remove((mNewValue, int(mTempId)))
                await broadcast_to_sockets(f"{event}^{mEffectedItem}^_")

            elif event == "changeDay":
                await broadcast_to_sockets(
                        f"{event}^{mEffectedItem}^{mNewValue}"
                        )
                mRaw = mEffectedItem.split("-")
                dayNo = outer_grid_map.index(mRaw[1])
                personNo = inner_grid_map.index(mRaw[0])
                grid[dayNo][personNo] = mNewValue

            elif event == "addNotice":

                if len(notices) == 5:
                    notices = notices[1:]

                notices.append(mNewValue)

                await broadcast_to_sockets(
                        f"{event}^_^{mNewValue}"
                        )

            elif event == "editItem":

                await broadcast_to_sockets(
                        f"{event}^{mEffectedItem}^{mNewValue}"
                        )

                removeIndex = -1

                for x, i in enumerate(all_items):
                    if i[1] == int(mEffectedItem):
                        removeIndex = x

                if removeIndex != -1:
                    all_items.remove(all_items[removeIndex])

                all_items.append((mNewValue, int(mEffectedItem)))

            elif event == "retrieveState":
                for item in all_items:
                    print("websocket sending")
                    await websocket.send_text(f"addItem^{item[1]}^{item[0]}")

                for notice in notices:
                    print("websocket sending notices")
                    await websocket.send_text(f"addNotice^_^{notice}")

                # only send for grid items that are not X by default

                f = (requests.get(url="https://xkcd.com/info.0.json")).json()
                top_number = int(f['num'])

                random_comic_number = int(top_number * random())

                print(f"https://xkcd.com/{random_comic_number}/info.0.json")
                t = (requests.get(
                    url=f"https://xkcd.com/{random_comic_number}/info.0.json"
                )).json()

                await websocket.send_text(f"changeComic^_^{t['img']}")

                await websocket.send_text(f"changeImageTitle^_^{t['alt']}")

                await websocket.send_text(
                    f"changeComicHref^_^https://xkcd.com/{t['num']}/"
                )

                for o in range(len(grid)):

                    for i in range(len(grid[0])):

                        if grid[o][i] != 'X':

                            tValue = grid[o][i]
                            day = outer_grid_map[o]
                            person = inner_grid_map[i]
                            await websocket.send_text(
                                f"changeDay^{person}-{day}^{tValue}"
                            )

    except WebSocketDisconnect:
        # not the best move neccessarily, but
        print("removed connection")
        all_connections.remove(websocket)

        # once again, saving state to disk
        print("saving to file on close...")

        with open(GRID_RESOURCES, "w") as gridState:

            for row in grid:
                gridState.write(",".join(row) + '\n')

        with open(LIST_RESOURCES, "w") as listItems:
            for item in all_items:
                listItems.write(f"{item[0]}^{item[1]}" + '\n')

        with open(NOTE_RESOURCES, "w") as noticeFile:

            noticeFile.write("\n".join(notices))


# Calculating the time remaining until monday
# TODO @robert - holy shit this is an abomination
def get_time_to_monday() -> int:
    now = datetime.now()

    weekdayToday = now.weekday()
    nextMondayTime = timedelta(6 - weekdayToday)
    changeInHours = timedelta(hours=23 - now.hour)
    changeInMinutes = timedelta(minutes=59 - now.minute)
    changeInSeconds = timedelta(seconds=59 - now.second)

    timediff = (
        now.today() + changeInHours
        + changeInMinutes + changeInSeconds + nextMondayTime
    ) - now

    print(f"Time difference to monday: {timediff}")

    timeDiffSecondsMonday = timediff.total_seconds()

    return timeDiffSecondsMonday


# timer for resetting each monday
async def start_timer(time: int):

    print("timer running")
    await asyncio.sleep(time)
    print("timer sleep over")

    # do something
    for o in range(len(grid)):

        for i in range(len(grid[0])):

            tValue = "E"
            day = outer_grid_map[o]
            person = inner_grid_map[i]
            await broadcast_to_sockets(f"changeDay^{person}-{day}^{tValue}")
            grid[o][i] = "E"

    await start_timer(get_time_to_monday())


def start_monday_timer():
    asyncio.ensure_future(start_timer(get_time_to_monday()))


start_monday_timer()
print("Started timer")


async def broadcast_to_sockets(data: str):
    for socket in all_connections:
        await socket.send_text(data)

# TODO @robert - timer for updating weekday show each day
# TODO @robert - timer for updating comic each day
