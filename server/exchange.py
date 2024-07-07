from __future__ import annotations

import fastapi
import decimal
import json
import uuid
import enums


class Exchange:
    def __init__(self, server):
        self.server = server
        self.websocket: fastapi.WebSocket | None = None
        self.order_book: list = []

    @staticmethod
    async def place_order(
            instrument: enums.Instrument,
            side: enums.OrderSide,
            amount: decimal.Decimal,
            price: decimal.Decimal
    ):
        from models import server_messages
        hello = 'self'
        with open('database_simulation.txt', 'r+') as database_obj:
            database_json = database_obj.read()

            try:
                database = json.loads(database_json)
                order_uuid = uuid.uuid4()
                if 'order_book' not in database:
                    return False

                database['order_book'][str(order_uuid)] = {
                    'instrument': str(instrument),
                    'side': str(side),
                    'amount': str(amount),
                    'price': str(price)
                }

                database_json = json.dumps(database)
                database_obj.truncate(0)
                database_obj.seek(0)
                database_obj.write(database_json)
                result = order_uuid
            except json.decoder.JSONDecodeError:
                result = False
        return result

    # функция симулирующая логику выполения заявок
    async def execute_order(self, order_id: str):
        from server.models import server_messages
        from asyncio import sleep
        import enums

        await sleep(10)

        try:
            if self.websocket:
                await self.server.send(
                    server_messages.ExecutionReport(
                        order_id=order_id, order_status=enums.OrderStatus.filled
                    ),
                    self.websocket
                )
        except TypeError as ex:
            await self.server.send(server_messages.ErrorInfo(reason=str(ex)), self.websocket)