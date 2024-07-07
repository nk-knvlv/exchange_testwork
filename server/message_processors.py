from __future__ import annotations

import asyncio
import uuid
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

    with open('database_simulation.txt', 'r+') as database_obj:
        database_json = database_obj.read()
        uuid_hash_str = f"{user_address}-{instrument}"
        subscription_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, uuid_hash_str))
        try:
            database = json.loads(database_json)
            # после реализации авторизации появится проверка на пользователя TODO

            if user_address not in database['users']:
                database['users'][user_address] = {
                    subscription_id: instrument
                }
                result_message = server_messages.SuccessInfo(message=str(subscription_id))
            else:
                if subscription_id in database['users'][user_address]:
                    return server_messages.ErrorInfo(reason='Subscription already exists')
                else:
                    database['users'][user_address][subscription_id] = instrument

            database_json = json.dumps(database)
            database_obj.truncate(0)
            database_obj.seek(0)
            database_obj.write(database_json)
        except json.decoder.JSONDecodeError:
            result_message = server_messages.ErrorInfo(reason='DB error')

    return result_message


async def unsubscribe_market_data_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.UnsubscribeMarketData,
):
    from server.models import server_messages
    import json

    user_address = websocket.client.host  # тут должен быть user_id когда реализуем авторизацию TODO
    subscription_id = str(message.subscription_id)
    with open('database_simulation.txt', 'r+') as database_obj:
        database_json = database_obj.read()

        try:
            database = json.loads(database_json)

            if user_address in database['users']:
                if subscription_id not in database['users'][user_address]:
                    result_message = server_messages.ErrorInfo(reason='The subscription does not exist')
                else:
                    del database['users'][user_address][subscription_id]
                    database_json = json.dumps(database)
                    database_obj.truncate(0)
                    database_obj.seek(0)
                    database_obj.write(database_json)
                    result_message = server_messages.SuccessInfo(message='Successfully unsubscribe')
            else:
                result_message = server_messages.ErrorInfo(reason="User doesn't exist")
        except json.decoder.JSONDecodeError:
            result_message = server_messages.ErrorInfo(reason='DB error')

    return result_message


async def place_order_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.PlaceOrder,
):
    from server.models import server_messages
    instrument = message.instrument
    side = message.side
    price = message.price
    amount = message.amount
    place_order_result = await server.exchange.place_order(instrument=instrument, side=side, amount=amount, price=price)
    if place_order_result:
        return server_messages.SuccessInfo(message=f'Order successfully placed. Order_id: {str(place_order_result)}')
    else:
        return server_messages.ErrorInfo(reason="DB error")


async def cancel_order_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.PlaceOrder,
):
    from server.models import server_messages
    order_id = message.order_id
    cancel_order_result = await server.exchange.cancel_order(order_id=order_id)
    if cancel_order_result:
        return server_messages.SuccessInfo(message=f'Order with {str(order_id)} id successfully canceled.')
    else:
        return server_messages.ErrorInfo(reason="Can't cancel order")
