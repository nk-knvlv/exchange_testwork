import uvicorn
import mimetypes
import pathlib

import fastapi

import ntpro_server

api = fastapi.FastAPI()
server = ntpro_server.NTProServer()
html = pathlib.Path('../client/index.html').read_text()


@api.get('/home')
async def get():
    return fastapi.responses.HTMLResponse(html)


@api.get('/static/{path}')
async def get(path: pathlib.Path):
    static_file = (pathlib.Path('static') / path).read_text()
    mime_type, encoding = mimetypes.guess_type(path)
    return fastapi.responses.PlainTextResponse(static_file, media_type=mime_type)


@api.websocket('/ws')
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await server.connect(websocket)

    try:
        await server.serve(websocket)
    except fastapi.WebSocketDisconnect:
        server.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)