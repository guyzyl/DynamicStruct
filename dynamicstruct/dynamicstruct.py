import struct
from typing import List, Any, Dict, Union
from collections import OrderedDict
from dataclasses import replace

from dynamicstruct import DynamicStructField


class DynamicStruct:
    """
    The purpose of DynamicStruct is to easily define new binary message formats
        and reuse them, without having to write a new class for each format.
    To define a new DynamicStruct, create a subclass and set `fields` to a list of `DynamicStructField` objects.

    For example:
    ```
    HelloMessage(DynamicStruct):
        fields = [
            DynamicStructField(name="hello", struct="b", default=1),
            DynamicStructField(name="world"),
            DynamicStructField(name="payload", struct="s", match_length=True),
        ]

        def on_pack(self):
            self.world = not self.world

    m = HelloMessage(world=1, payload=b"hello world")
    print(m.world)
    packed = m.pack()
    mm = HelloMessage.from_buffer(packed)
    ```
    """

    fields: List[DynamicStructField] = []
    _fields: OrderedDict[str, DynamicStructField] = OrderedDict()
    endian_struct: str = "<"

    def __init__(self, **kwargs) -> None:
        """
        The reason why we copy fields to _fields is because fields contains objects that are shared across all instances of the class.
        """
        # Copy fields
        self.__dict__["_fields"] = OrderedDict(
            (k.name, replace(k)) for k in self.fields
        )
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __getattr__(self, name: str) -> Any:
        if name in self._fields:
            return self._fields[name].value or self._fields[name].default
        raise NameError(f"Field '{name}' is not defined")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._fields:
            self._fields[name].value = value
        else:
            raise NameError(f"Field '{name}' is not defined")

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self._fields.values}>"

    @property
    def struct(self) -> str:
        """
        The joint struct of all fields.
        """
        return self.endian_struct + "".join(
            [
                f"{f.length if f.length != 1 else ''}{f.struct}"
                for f in self._fields.values()
            ]
        )

    @property
    def size(self) -> int:
        """
        The size of the struct.
        """
        return struct.calcsize(self.struct)

    @property
    def values(self) -> Dict[str, Union[int, bytes]]:
        """
        Return a dict of all fields and their values.
        """
        return {k: getattr(self, k) for k in self._fields}

    @classmethod
    def from_buffer(cls, buffer: bytes, validate: bool = True) -> "DynamicStruct":
        """
        Create a new instance of the class from a buffer.
        """
        instance = cls()
        instance.unpack(buffer, validate=validate)
        return instance

    def _set_length(self) -> None:
        """
        Set the length of the fields that have `match_length` set to True.
        """
        for field in self._fields.values():
            if field.match_length:
                field.value = self.size

    def _set_match_length_pack(self) -> None:
        """
        Set the length of the fields that have `match_length` set to True.
        """
        for field in self._fields.values():
            if field.match_length:
                field.length = len(field.value)

    def _set_match_length_unpack(self, buffer_length: int) -> None:
        """
        Update the lngth attribute of the fields that have `match_length` set to True.
        """
        match_fields = [f for f in self._fields.values() if f.match_length]
        if len(match_fields) > 1:
            raise ValueError("Only one field can have match_length set to True")
        if len(match_fields) == 1:
            match_fields[0].length = 0
            match_fields[0].length = buffer_length - self.size

    def on_pack(self) -> None:
        """
        A function that's called before packing.
        """
        ...

    def is_valid(self) -> bool:
        """
        Check if instance is valid after unpacking.
        """
        return True

    def pack(self) -> bytes:
        """
        Pack the instance into a buffer.
        """
        self._set_match_length()
        self.on_pack()
        return struct.pack(self.struct, *self.values)

    def unpack(self, buffer: bytes, validate: bool = True) -> None:
        """
        Unpack a buffer into the instance.
        """
        self._set_match_length_unpack(len(buffer))
        values = struct.unpack(self.struct, buffer)

        for field, value in zip(self._fields.values(), values):
            field.value = value

        if validate and not self.is_valid():
            raise ValueError("Failed to validate instance")
