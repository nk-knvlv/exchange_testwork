from __future__ import annotations

import uuid
from typing import TypeVar

import bidict as bidict

from server import enums
from server.models.base import Envelope, Message, Quote


class ServerMessage(Message):
    def get_type(self: ServerMessageT) -> enums.ServerMessageType:
        return _SERVER_MESSAGE_TYPE_BY_CLASS[self.__class__]


class ErrorInfo(ServerMessage):
    reason: str


class SuccessInfo(ServerMessage):
    message: str


class ExecutionReport(ServerMessage):
    order_id: uuid.UUID
    order_status: enums.OrderStatus

    # выдает ошибку при парсинге uuid в json
    def dict(self, *args, **kwargs):
        values = super().dict(*args, **kwargs)
        values['order_id'] = str(values['order_id'])  # Преобразование uuid в строку
        return values


class MarketDataUpdate(ServerMessage):
    subscription_id: uuid.UUID
    instrument: enums.Instrument
    quotes: list[Quote]

    def dict(self, *args, **kwargs):
        values = super().dict(*args, **kwargs)
        values['subscription_id'] = str(values['subscription_id'])  # Преобразование uuid в строку
        for quote in values['quotes']:
            for key, value in quote.items():
                quote[key] = str(value)
        return values


class ServerEnvelope(Envelope):
    message_type: enums.ServerMessageType

    def get_parsed_message(self):
        return _SERVER_MESSAGE_TYPE_BY_CLASS.inverse[self.message_type].parse_obj(self.message)


_SERVER_MESSAGE_TYPE_BY_CLASS = bidict.bidict({
    SuccessInfo: enums.ServerMessageType.success,
    ErrorInfo: enums.ServerMessageType.error,
    ExecutionReport: enums.ServerMessageType.execution_report,
    MarketDataUpdate: enums.ServerMessageType.market_data_update,
})
ServerMessageT = TypeVar('ServerMessageT', bound=ServerMessage)
