import uvicorn
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
    return templates.TemplateResponse("index.html", {"request": request})

# websocket and state handling
all_connections = []


# format of a tuple: (ITEMNAME, ITEMID)
# i am loading these into array, because like
# i dont wanna deal with that much disk IO
all_items: list[tuple] = []

# grid format: [STATE_1, STATE_2, STATE_3, STATE_4] for each weekday
# STATES = E, X, ?, O
grid: list[list[str]] = []
global item_count
item_count = 0

# load the initially saved items
with open("list_items", "r") as itemsFile:
    raw_items = itemsFile.readlines()
    for raw in raw_items:
        t = raw.replace('\n', "")
        if t == "": continue
        t = t.split("^")
        print(t)
        item_id = int(t[1])
        if item_id >= item_count:
            item_count = item_id + 1
        all_items.append((t[0], item_id))

with open("grid_state", "r") as gridFile:
    raw_grid = gridFile.readlines()

    for raw in raw_grid:
        tRaw = raw.replace("\n", "")
        grid.append(tRaw.split(","))

    print("Finished Grid:", grid)

@app.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    all_connections.append(websocket)
    global item_count

    outer_grid_map = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    inner_grid_map = ["rick", "youri", "robert", "milan"]

    try:
        while True:
            data = await websocket.receive_text()
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
                grid[dayNo][personNo] = mNewValue if mNewValue != "<space></space>" else "E"

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

                # only send for grid items that are not X by default


                for o in range(len(grid)):

                    for i in range(len(grid[0])):

                        if grid[o][i] != 'X':

                            tValue = grid[o][i] if grid[o][i] != 'E' else "<space></space>"
                            day = outer_grid_map[o]
                            person = inner_grid_map[i]
                            await websocket.send_text(f"changeDay^{person}-{day}^{tValue}")

    except WebSocketDisconnect:
        # not the best move neccessarily, but
        print("removed connection")
        all_connections.remove(websocket)

        # once again, saving state to disk
        print("saving to file on close...")
        
        with open("grid_state", "w") as gridState:

            for row in grid:
                gridState.write(",".join(row) + '\n')

        with open("list_items", "w") as listItems:
            for item in all_items:
                listItems.write(f"{item[0]}^{item[1]}" + '\n')


async def broadcast_to_sockets(data: str):
    for socket in all_connections:
        await socket.send_text(data)

if __name__ == "__main__":

    uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=80,
            reload=True
            )
    """
    uvicorn.run(
            "main:app",
            port=8000
            )
    """


