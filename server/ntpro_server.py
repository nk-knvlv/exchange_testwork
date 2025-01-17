import fastapi
import pydantic
import starlette.datastructures

from models import client_messages, server_messages, base
from exchange import Exchange


class NTProServer:
    def __init__(self):
        self.connections: dict[starlette.datastructures.Address, base.Connection] = {}
        self.exchange = Exchange()

    async def connect(self, websocket: fastapi.WebSocket):
        await websocket.accept()
        self.connections[websocket.client] = base.Connection()

    def disconnect(self, websocket: fastapi.WebSocket):
        self.connections.pop(websocket.client)

    async def serve(self, websocket: fastapi.WebSocket):
        while True:
            raw_envelope = await websocket.receive_json()

            try:
                envelope = client_messages.ClientEnvelope.parse_obj(raw_envelope)
                message = envelope.get_parsed_message()
            except pydantic.ValidationError as ex:
                await self.send(server_messages.ErrorInfo(reason=str(ex)), websocket)
                continue

            response = await message.process(self, websocket)

            await self.send(response, websocket)

    @staticmethod
    async def send(message: base.MessageT, websocket: fastapi.WebSocket):
        await websocket.send_json(server_messages.ServerEnvelope(message_type=message.get_type(),
                                                                 message=message.dict()).dict())
