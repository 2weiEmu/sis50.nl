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

current_items: list[str] = []

with open("all_shopping_items", "r") as itemsfile:
    current_items = itemsfile.readlines()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

all_connections = []


@app.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    all_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            if data.startswith("new_item-"):
                #await websocket.send_text(f"{data}")
                await broadcast_to_sockets(f"{data}")

            elif data.startswith("del_item-"):
                #await websocket.send_text(f"{data}")
                await broadcast_to_sockets(f"{data}")
            elif data.startswith("change_day-"):
                await broadcast_to_sockets(f"{data}")
                
    except WebSocketDisconnect:
        print("removed connection")
        all_connections.remove(websocket)


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
