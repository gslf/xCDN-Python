"""AST types for xCDN.

The AST is intentionally decoupled from parsing/serialization so it can be
constructed or consumed programmatically.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union
from decimal import Decimal
from datetime import datetime
from uuid import UUID


@dataclass
class Document:
    """This struct represent a whole xCDN document."""
    prolog: List['Directive'] = field(default_factory=list)
    values: List['Node'] = field(default_factory=list)

    @staticmethod
    def new() -> 'Document':
        """Construct an empty document."""
        return Document()


@dataclass
class Directive:
    """A prolog directive, e.g. `$schema: "..."`."""
    name: str  # without the leading '$'
    value: 'Value'


@dataclass
class Node:
    """A value enriched with optional `#tags` and `@annotations`."""
    tags: List['Tag'] = field(default_factory=list)
    annotations: List['Annotation'] = field(default_factory=list)
    value: 'Value' = None

    @staticmethod
    def new(value: 'Value') -> 'Node':
        return Node(value=value)


@dataclass
class Tag:
    """A tag like #demotag"""
    name: str

    def __hash__(self):
        return hash(self.name)


@dataclass
class Annotation:
    """An annotation like `@mime("image/png")`."""
    name: str
    args: List['Value'] = field(default_factory=list)


class ValueType:
    """Base class for all value types."""
    pass


@dataclass
class Null(ValueType):
    """Null value."""
    def __str__(self):
        return "null"


@dataclass
class Bool(ValueType):
    """Boolean value."""
    value: bool

    def __str__(self):
        return str(self.value).lower()


@dataclass
class Int(ValueType):
    """Integer value."""
    value: int

    def __str__(self):
        return str(self.value)


@dataclass
class Float(ValueType):
    """Float value."""
    value: float

    def __str__(self):
        return str(self.value)


@dataclass
class DecimalValue(ValueType):
    """Arbitrary-precision decimal. Serialized as `d"..."`."""
    value: Decimal

    def __str__(self):
        return str(self.value)


@dataclass
class String(ValueType):
    """String value."""
    value: str

    def __str__(self):
        return self.value


@dataclass
class Bytes(ValueType):
    """Bytes decoded from Base64 (standard or URL-safe). Serialized as `b"..."`."""
    value: bytes

    def __str__(self):
        return f"<{len(self.value)} bytes>"


@dataclass
class DateTime(ValueType):
    """RFC3339 datetime. Serialized as `t"..."`."""
    value: datetime

    def __str__(self):
        return self.value.isoformat()


@dataclass
class Duration(ValueType):
    """ISO8601 duration: `PnYnMnDTnHnMnS`. Serialized as `r"..."`."""
    value: str  # We'll store as string for simplicity

    def __str__(self):
        return "<duration>"


@dataclass
class Uuid(ValueType):
    """UUID v1-v8."""
    value: UUID

    def __str__(self):
        return str(self.value)


@dataclass
class Array(ValueType):
    """Array value."""
    value: List[Node] = field(default_factory=list)

    def __str__(self):
        return f"[{len(self.value)} items]"


@dataclass
class Object(ValueType):
    """An ordered map to preserve insertion order during roundtrips."""
    value: Dict[str, Node] = field(default_factory=dict)

    def __str__(self):
        return f"{{{len(self.value)} entries}}"


# Type alias for convenience
Value = Union[
    Null, Bool, Int, Float, DecimalValue, String, Bytes,
    DateTime, Duration, Uuid, Array, Object
]
