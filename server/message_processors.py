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
    import uuid
    from server.models import server_messages

    instrument = str(message.instrument.value)
    client_subscriptions = server.connections[websocket.client].subscriptions

    uuid_hash_str = f"{instrument}-{websocket.client}"
    subscription_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, uuid_hash_str))

    if subscription_id not in client_subscriptions:
        # добавить подписку подключению
        client_subscriptions[subscription_id] = instrument
        # добавить подписчика инструменту
        server.exchange.instruments[instrument].subscription.subscribers[subscription_id] = websocket
        result_message = server_messages.SuccessInfo(message=subscription_id)
    else:
        result_message = server_messages.ErrorInfo(reason='Subscription already exist')

    return result_message


async def unsubscribe_market_data_processor(
        server: NTProServer,
        websocket: fastapi.WebSocket,
        message: client_messages.UnsubscribeMarketData,
):
    from server.models import server_messages
    subscription_id = str(message.subscription_id)
    client_subscriptions = server.connections[websocket.client].subscriptions
    if subscription_id in client_subscriptions:
        ticker = client_subscriptions[subscription_id]
        # добавить подписку подключению
        del client_subscriptions[subscription_id]
        # добавить подписчика инструменту
        instrument = server.exchange.instruments[ticker]
        del instrument.subscription.subscribers[subscription_id]

        result_message = server_messages.SuccessInfo(message='Successfully unsubscribe')
    else:
        result_message = server_messages.ErrorInfo(reason='Subscription does not exists')

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

    try:
        place_order_result = await server.exchange.place_order(
            instrument=instrument,
            side=side,
            amount=amount,
            price=price,
            websocket=websocket
        )
        result_message = server_messages.SuccessInfo(
            message=f'Order successfully placed. Order_id: {str(place_order_result)}'
        )
    except server.exchange.ExchangeException as ex:
        result_message = server_messages.ErrorInfo(reason=(str(ex)))

    return result_message


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
