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
        self.executing_tasks_group = {}

    async def place_order(
            self,
            instrument: enums.Instrument,
            side: enums.OrderSide,
            amount: decimal.Decimal,
            price: decimal.Decimal
    ):
        from models import server_messages
        from asyncio import create_task
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
                    'price': str(price),
                    'order_status': enums.OrderStatus.active
                }

                database_json = json.dumps(database)
                database_obj.truncate(0)
                database_obj.seek(0)
                database_obj.write(database_json)
                result = order_uuid
                order_id = str(order_uuid)

                task = create_task(self.server.exchange.execute_order(order_id))
                self.executing_tasks_group[order_id] = task

            except json.decoder.JSONDecodeError:
                result = False
        return result

    # функция симулирующая логику выполения заявок
    async def execute_order(self, order_id: str):
        from server.models import server_messages
        from asyncio import sleep
        import random
        import enums
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
                    if self.websocket:
                        await self.server.send(
                            server_messages.ExecutionReport(
                                order_id=order_id, order_status=executed_order_status_value
                            ),
                            self.websocket
                        )
                except Exception as ex:
                    await self.server.send(server_messages.ErrorInfo(reason=str(ex)), self.websocket)

            except json.decoder.JSONDecodeError:
                await self.server.send(server_messages.ErrorInfo(reason='DB error'), self.websocket)

    async def cancel_order(self, order_id: str):
        from server.models import server_messages
        import enums

        # по order_id находим и отменяем отложенное выполнение
        if order_id in self.executing_tasks_group:
            self.executing_tasks_group[order_id].cancel()
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
            except json.decoder.JSONDecodeError:
                return False

        return True