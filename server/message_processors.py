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
    import uuid
    user_address = websocket.client.host  # тут должен быть user_id когда реализуем авторизацию TODO
    instrument = str(message.instrument.value)

    with open('database_simulation.txt', 'r+') as database:
        subscriptions_json = database.read()
        uuid_hash_str = f"{user_address}-{instrument}"
        subscription_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, uuid_hash_str))

        try:
            subscriptions = json.loads(subscriptions_json)

            if subscription_id not in subscriptions[user_address]:
                subscriptions[user_address][subscription_id] = instrument
        # если такой подписки нет, добавляем
        except json.decoder.JSONDecodeError:
            subscriptions: dict[str, dict] = {user_address: {subscription_id: instrument}}

        subscriptions_json = json.dumps(subscriptions)
        database.truncate(0)
        database.seek(0)
        database.write(subscriptions_json)

        return server_messages.SuccessInfo(message=str(subscription_id))


async def unsubscribe_market_data_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.UnsubscribeMarketData,
):
    from server.models import server_messages
    import json

    user_address = websocket.client.host  # тут должен быть user_id когда реализуем авторизацию TODO
    subscription_id = str(message.subscription_id)

    with open('database_simulation.txt', 'r+') as database:
        subscriptions_json = database.read()

        try:
            subscriptions = json.loads(subscriptions_json)

            if subscription_id in subscriptions[user_address]:
                del subscriptions[user_address][subscription_id]
        # если такой подписки нет, добавляем
        except json.decoder.JSONDecodeError:
            pass
        subscriptions_json = json.dumps(subscriptions)
        database.truncate(0)
        database.seek(0)
        database.write(subscriptions_json)

        return server_messages.SuccessInfo(message=str('Successfully unsubscribe'))


async def place_order_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.PlaceOrder,
):
    from server.models import server_messages

    # TODO ...

    return server_messages.SuccessInfo()
