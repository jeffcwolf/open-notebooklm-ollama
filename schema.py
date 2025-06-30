"""
schema.py
"""

from typing import Literal, List

from pydantic import BaseModel, Field


class DialogueItem(BaseModel):
    """A single dialogue item."""

    speaker: Literal["Host (Jane)", "Guest"]
    text: str


class ShortDialogue(BaseModel):
    """The dialogue between the host and guest."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 11 to 17 items"
    )


class MediumDialogue(BaseModel):
    """The dialogue between the host and guest."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 19 to 29 items"
    )


class LongDialogue(BaseModel):
    """The dialogue between the host and guest for longer content."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 35 to 50 items"
    )


class ExtendedDialogue(BaseModel):
    """The dialogue between the host and guest for extended content."""

    scratchpad: str
    name_of_guest: str
    dialogue: List[DialogueItem] = Field(
        ..., description="A list of dialogue items, typically between 50 to 70 items"
    )