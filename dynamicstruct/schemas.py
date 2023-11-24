from typing import Union
from dataclasses import dataclass


@dataclass
class DynamicStructField:
    """
    A single field in a DynamicStruct.
    :param name: The name of the field.
    :param struct: The struct format character to be used for the field.
        By default "B" (byte) is used.
    :param length: The number of self.struct characters to be used for the field.
        By default 1 is used.
    :param default: The default value.
    :param value: The actual value of the field (or None).
    :param match_length: Whether the length of the field to the number of remaining bytes.
        This should be used on "payload" fields where the length may vary.
        Can only be used once per DynamicStruct.
    """

    name: str
    struct: str = "B"
    length: int = 1
    default: Union[int, bytes] = 0
    value: Union[int, bytes, None] = None
    match_length: bool = False
