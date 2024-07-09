from __future__ import annotations

import asyncio

import fastapi
import decimal
import json
import uuid
import enums
from models import base


class Exchange:
    websocket: fastapi.WebSocket
    instruments: dict[str, Instrument]
    executing_order_group: dict[str, asyncio.Task]
    server: object | None

    def __init__(self):
        self.server = None
        self.instruments = {}
        self.websocket: fastapi.WebSocket | None = None
        self.order_book: list = []  # нужно ли мне это TODO
        self.executing_order_group = {}

    class ExchangeException(Exception):
        def __init__(self, message, additional_data=None):
            super().__init__(message)
            self.additional_data = additional_data

    class Subscription:
        server: object
        subscribers: dict[str, fastapi.WebSocket.client]

        def __init__(self, server):
            self.server = server
            self.subscribers = {}

        # notify в Субъекте
        async def notify_subscribers(self, ticker, quotes):
            from server.models import server_messages
            # prepared_quotes = []
            # for quote in quotes:
            #     prepared_quotes.append(quote.dict())
            for subscription_id, websocket in self.subscribers.items():

                market_data = server_messages.MarketDataUpdate(
                    subscription_id=subscription_id,
                    instrument=ticker,
                    quotes=quotes
                )

                if websocket:
                    await self.server.send(market_data,
                                           websocket
                                           )

    # Субъект в обсервере
    class Instrument:
        ticker: enums.Instrument
        quotes: list[base.Quote]
        subscription: Exchange.Subscription

        def __init__(self, ticker, quotes, subscription):
            self.ticker = ticker
            self.quotes = quotes
            self.subscription = subscription

        # notify в Субъекте
        async def update_quotes(self):
            await self.subscription.notify_subscribers(self.ticker, self.quotes)

    def run_exchange(self, server):
        self.server = server
        self.instruments = self.get_instruments()

    async def stop_exchange(self):
        for task in self.executing_order_group.values():
            task.cancel()

    async def place_order(
            self,
            instrument: enums.Instrument,
            side: enums.OrderSide,
            amount: decimal.Decimal,
            price: decimal.Decimal,
            websocket
    ):
        from asyncio import create_task
        with open('database_simulation.txt', 'r+') as database_obj:
            database_json = database_obj.read()

            try:
                database = json.loads(database_json)
                order_uuid = uuid.uuid4()
                if 'order_book' not in database:
                    raise self.ExchangeException('DB error')

                database['order_book'][str(order_uuid)] = {
                    'instrument': str(instrument),
                    'side': str(side),
                    'amount': str(amount),
                    'price': str(price),
                    'order_status': enums.OrderStatus.active
                }

                database_json = json.dumps(database)
                database_obj.truncate(0)
                database_obj.seek(0)
                database_obj.write(database_json)
                result = order_uuid
                order_id = str(order_uuid)

                exchange_instrument = self.instruments[instrument]

                await exchange_instrument.update_quotes()

                task = create_task(self.execute_order(order_id, websocket))

                self.executing_order_group[order_id] = task

            except (json.decoder.JSONDecodeError, FileNotFoundError):
                raise self.ExchangeException('DB error')
        return result

    async def get_placed_orders(
            self
    ):
        with open('database_simulation.txt', 'r+') as database_obj:
            database_json = database_obj.read()

            try:
                database = json.loads(database_json)
                if 'order_book' in database:
                    self.order_book = database['order_book']
                    return
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                result = False
        return result

    # функция симулирующая логику выполения заявок
    async def execute_order(self, order_id: str, websocket):
        from server.models import server_messages
        from asyncio import sleep
        import random
        # симуляция выполнения
        await sleep(20)

        executed_order_status_value = random.randint(2, 4)

        with open('database_simulation.txt', 'r+') as database_obj:
            database_json = database_obj.read()

            try:
                database = json.loads(database_json)

                if 'order_book' not in database:
                    return False

                database['order_book'][order_id]['order_status'] = executed_order_status_value
                database_json = json.dumps(database)
                database_obj.truncate(0)
                database_obj.seek(0)
                database_obj.write(database_json)

                try:
                    if websocket:
                        await self.server.send(
                            server_messages.ExecutionReport(
                                order_id=order_id, order_status=executed_order_status_value
                            ),
                            websocket
                        )
                except Exception as ex:
                    await self.server.send(server_messages.ErrorInfo(reason=str(ex)), websocket)

            except (json.decoder.JSONDecodeError, FileNotFoundError):
                await self.server.send(server_messages.ErrorInfo(reason='DB error'), websocket)

    async def cancel_order(self, order_id: str):
        import enums

        # по order_id находим и отменяем отложенное выполнение
        if order_id in self.executing_order_group:
            self.executing_order_group[order_id].cancel()
        else:
            return False

        # обновляем из базы данных
        with open('database_simulation.txt', 'r+') as database_obj:
            database_json = database_obj.read()

            try:
                database = json.loads(database_json)

                if 'order_book' not in database:
                    return False

                database['order_book'][order_id]['order_status'] = enums.OrderStatus.cancelled
                database_json = json.dumps(database)
                database_obj.truncate(0)
                database_obj.seek(0)
                database_obj.write(database_json)
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                return False

        return True

    def get_instruments(self):
        instruments = {}

        instrument_tickers = {instrument.value for instrument in enums.Instrument.__members__.values()}

        try:
            with open('database_simulation.txt', 'r+') as database_obj:
                database_json = database_obj.read()
                database = json.loads(database_json)
                for ticker in instrument_tickers:
                    subscription = self.Subscription(self.server)
                    instrument = self.Instrument(ticker=ticker, quotes=database['quotes'][ticker],
                                                 subscription=subscription)
                    instruments[ticker] = instrument
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            raise self.ExchangeException("DB error")
        return instruments
