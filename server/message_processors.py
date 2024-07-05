from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fastapi

    from server.models import client_messages
    from server.ntpro_server import NTProServer


async def subscribe_market_data_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.SubscribeMarketData,
):
    from server.models import server_messages
    import json
    user_address = websocket.client.host
    # получаем список подключений клиента
    with open('database_simulation.txt', 'r+') as database:
        subscribes_json = database.read()

        try:
            subscribes = json.loads(subscribes_json)
            if message.instrument.value not in subscribes[user_address]:
                subscribes[user_address].append(message.instrument.value)
        # если такой подписки нет, добавляем
        except json.decoder.JSONDecodeError:
            subscribes: dict[str, list[str]] = {user_address: [message.instrument.value]}

        subscribes_json = json.dumps(subscribes)
        database.truncate(0)
        database.seek(0)
        database.write(subscribes_json)
        return server_messages.SuccessInfo()


async def unsubscribe_market_data_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.UnsubscribeMarketData,
):
    from server.models import server_messages
    import json

    user_address = websocket.client.host
    # получаем список подключений клиента
    with open('database_simulation.txt', 'r+') as database:
        subscribes_json = database.read()

        try:
            subscribes = json.loads(subscribes_json)
            if message.instrument.value not in subscribes[user_address]:
                subscribes[user_address].append(message.instrument.value)
        # если такой подписки нет, добавляем
        except json.decoder.JSONDecodeError:
            subscribes: dict[str, list[str]] = {user_address: [message.instrument.value]}

        subscribes_json = json.dumps(subscribes)
        database.truncate(0)
        database.seek(0)
        database.write(subscribes_json)
        return server_messages.SuccessInfo()


async def place_order_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.PlaceOrder,
):
    from server.models import server_messages

    # TODO ...

    return server_messages.SuccessInfo()
