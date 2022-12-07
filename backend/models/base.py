from __future__ import annotations

import abc
import asyncio
import decimal
from typing import TypeVar

import pydantic

from backend.enums import ClientMessageType, ServerMessageType


class Envelope(pydantic.BaseModel, abc.ABC):
    class Config:
        extra = pydantic.Extra.forbid

    message_type: ClientMessageType | ServerMessageType
    message: dict

    @abc.abstractmethod
    def get_parsed_message(self): ...


class Message(pydantic.BaseModel, abc.ABC):
    class Config:
        frozen = True
        extra = pydantic.Extra.forbid

    @abc.abstractmethod
    def get_type(self): ...


class Connection(pydantic.BaseModel):
    class Config:
        arbitrary_types_allowed = True

    subscriptions: list[asyncio.Task] = []


class Quote(pydantic.BaseModel):
    bid: decimal.Decimal
    offer: decimal.Decimal
    min_amount: decimal.Decimal
    max_amount: decimal.Decimal


MessageT = TypeVar('MessageT', bound=Message)
