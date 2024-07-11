import pytest
from unittest.mock import AsyncMock, MagicMock
from server.message_processors import (
    subscribe_market_data_processor,
    unsubscribe_market_data_processor,
    place_order_processor,
    cancel_order_processor
)
from server.models import server_messages
from server import enums
from server.models import base

from bidict import bidict

# Создаем словарь соответствия
instrument_map = bidict({
    'EUR/USD': enums.Instrument.eur_usd,
    'EUR/RUB': enums.Instrument.eur_rub,
    'USD/RUB': enums.Instrument.usd_rub,
})


# создаем заглушки для NTProServer, fastapi.WebSocket и сообщения
class MockNTProServer:
    connections = {}  # создаем заглушку для connections
    exchange = AsyncMock()


class MockWebSocket:
    client = "test_client"


class MockClientMessage:
    instrument: enums.Instrument


# тест на успешную подписку
@pytest.mark.parametrize(
    "instrument_ticker, expected_result",
    [
        ("EUR/RUB", True),
        ("EUR/RUB", True),
        ("BTC/RUB", False),
    ]
)
@pytest.mark.asyncio
async def test_subscribe_market_data_processor_success(instrument_ticker, expected_result):
    # создаем экземпляры заглушек
    server = MockNTProServer()
    websocket = MockWebSocket()
    message = MockClientMessage()
    message.instrument = False

    server.connections[websocket.client] = base.Connection()
    for instrument in enums.Instrument:
        if instrument.value == instrument_ticker:
            message.instrument = instrument
    if message.instrument:
        # вызываем тестируемую функцию
        result = await subscribe_market_data_processor(server, websocket, message)
        assert isinstance(result.message, str) == expected_result
        assert (server.connections["test_client"].subscriptions[result.message] == instrument_ticker) == expected_result
    else:
        assert message.instrument != bool


# тест на успешное отписывание
@pytest.mark.parametrize(
    "subscription_id, unsubscription_id, expected_result",
    [
        ('7f487b3e-59d7-4ec9-b75d-0f0f0e9bbe7a', '7f487b3e-59d7-4ec9-b75d-0f0f0e9bbe7a', True),
    ]
)
@pytest.mark.asyncio
async def test_unsubscribe_market_data_processor_success(
        subscription_id,
        unsubscription_id,
        expected_result
):
    # создаем экземпляры заглушек
    server = MockNTProServer()
    websocket = MockWebSocket()
    message = MockClientMessage()
    instrument = "EUR/RUB"

    server.connections[websocket.client] = base.Connection()
    message.subscription_id = unsubscription_id
    # вызываем тестируемую функцию

    client_subscriptions = server.connections[websocket.client].subscriptions
    client_subscriptions[subscription_id] = instrument
    server.exchange.instruments[instrument].subscription.subscribers[subscription_id] = websocket

    result = await unsubscribe_market_data_processor(server, websocket, message)

    assert (isinstance(result, server_messages.SuccessInfo)) == expected_result
    assert (subscription_id not in client_subscriptions) == expected_result
    assert (subscription_id not in server.exchange.instruments[instrument].subscription.subscribers) == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "instrument_ticker, side, amount, price, expected_result",
    [
        ("EUR/RUB", "buy", 100, 75.5, True),
        ("USD/EUR", "sell", 150, 80.3, True),
    ]
)
async def test_place_order_processor(instrument_ticker, side, amount, price, expected_result):
    # Создание экземпляров заглушек (mocks) для сервера и веб-сокета
    server_mock = MockNTProServer()
    websocket_mock = MockWebSocket()
    message_mock = MockClientMessage()
    message_mock.instrument = instrument_ticker
    message_mock.side = side
    message_mock.amount = amount
    message_mock.price = price
    # Вызов асинхронной функции и ожидание результата
    result = await place_order_processor(server_mock, websocket_mock, message_mock)

    # Проверка ожидаемого результата
    if expected_result:
        assert isinstance(result, server_messages.SuccessInfo)
    else:
        assert isinstance(result, server_messages.ErrorInfo)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "order_id, cancel_order_result, expected_result",
    [
        ("order123", True, True),  # успешная отмена заказа
        ("order456", False, False),  # неудачная отмена заказа
        ("order789", True, True),  # успешная отмена заказа
        ("order100", False, False),  # неудачная отмена заказа
    ]
)
async def test_cancel_order_processor(order_id, cancel_order_result, expected_result):
    # Создание экземпляров заглушек (mocks) для сервера и веб-сокета
    server_mock = MockNTProServer()
    websocket_mock = MockWebSocket()
    message_mock = MockClientMessage()

    # Имитация возврата значения от сервера.exchange.cancel_order()
    server_mock.exchange.cancel_order = AsyncMock(return_value=cancel_order_result)

    # Создание сообщения с переданным order_id
    message_mock.order_id = order_id

    # Вызов асинхронной функции и ожидание результата
    result = await cancel_order_processor(server_mock, websocket_mock, message_mock)

    # Проверка ожидаемого результата
    if expected_result:
        assert isinstance(result, server_messages.SuccessInfo)
    else:
        assert isinstance(result, server_messages.ErrorInfo)
