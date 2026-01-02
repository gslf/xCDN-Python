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

    def __getitem__(self, key: Union[str, int]):
        """Access document values directly.
        
        If key is int: access by index in values list.
        If key is str: access first value as object and get the key.
        """
        if isinstance(key, int):
            return self.values[key]
        elif isinstance(key, str):
            # Assume first value is an Object and get the key from it
            if self.values and isinstance(self.values[0].value, Object):
                return self.values[0].value[key]
            raise KeyError(f"Cannot access key '{key}' on document")
        raise TypeError(f"Document indices must be integers or strings, not {type(key).__name__}")

    def __setitem__(self, key: Union[str, int], value):
        """Set document values directly."""
        if isinstance(key, int):
            self.values[key] = value if isinstance(value, Node) else Node.new(value)
        elif isinstance(key, str):
            # Ensure first value is an Object
            if not self.values:
                self.values.append(Node.new(Object()))
            if isinstance(self.values[0].value, Object):
                self.values[0].value[key] = value
            else:
                raise TypeError("First document value is not an Object")
        else:
            raise TypeError(f"Document indices must be integers or strings, not {type(key).__name__}")

    def __contains__(self, key: str) -> bool:
        """Check if key exists in first object value."""
        if self.values and isinstance(self.values[0].value, Object):
            return key in self.values[0].value
        return False


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

    def __getitem__(self, key: Union[str, int]):
        """Delegate item access to the underlying value."""
        return self.value[key]

    def __setitem__(self, key: Union[str, int], value):
        """Delegate item setting to the underlying value."""
        self.value[key] = value

    def __contains__(self, key: Union[str, int]) -> bool:
        """Delegate containment check to the underlying value."""
        return key in self.value

    def __iter__(self):
        """Delegate iteration to the underlying value."""
        return iter(self.value)

    def __len__(self) -> int:
        """Delegate length to the underlying value."""
        return len(self.value)

    def get(self, key: str, default=None):
        """Delegate get() to the underlying value (for Object types)."""
        if hasattr(self.value, 'get'):
            return self.value.get(key, default)
        raise AttributeError(f"'{type(self.value).__name__}' object has no attribute 'get'")

    def keys(self):
        """Delegate keys() to the underlying value (for Object types)."""
        if hasattr(self.value, 'keys'):
            return self.value.keys()
        raise AttributeError(f"'{type(self.value).__name__}' object has no attribute 'keys'")

    def values_iter(self):
        """Delegate values_iter() to the underlying value (for Object types)."""
        if hasattr(self.value, 'values_iter'):
            return self.value.values_iter()
        raise AttributeError(f"'{type(self.value).__name__}' object has no attribute 'values_iter'")

    def items(self):
        """Delegate items() to the underlying value (for Object types)."""
        if hasattr(self.value, 'items'):
            return self.value.items()
        raise AttributeError(f"'{type(self.value).__name__}' object has no attribute 'items'")

    def append(self, value):
        """Delegate append() to the underlying value (for Array types)."""
        if hasattr(self.value, 'append'):
            return self.value.append(value)
        raise AttributeError(f"'{type(self.value).__name__}' object has no attribute 'append'")


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

    def __getitem__(self, index: int):
        """Access array items by index."""
        return self.value[index]

    def __setitem__(self, index: int, value):
        """Set array items by index."""
        self.value[index] = value if isinstance(value, Node) else Node.new(value)

    def __len__(self) -> int:
        """Return array length."""
        return len(self.value)

    def __iter__(self):
        """Iterate over array items."""
        return iter(self.value)

    def append(self, value):
        """Append value to array."""
        self.value.append(value if isinstance(value, Node) else Node.new(value))


@dataclass
class Object(ValueType):
    """An ordered map to preserve insertion order during roundtrips."""
    value: Dict[str, Node] = field(default_factory=dict)

    def __str__(self):
        return f"{{{len(self.value)} entries}}"

    def __getitem__(self, key: str):
        """Access object values by key."""
        return self.value[key]

    def __setitem__(self, key: str, value):
        """Set object values by key."""
        self.value[key] = value if isinstance(value, Node) else Node.new(value)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in object."""
        return key in self.value

    def __iter__(self):
        """Iterate over object keys."""
        return iter(self.value)

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.value)

    def get(self, key: str, default=None):
        """Get value with default fallback."""
        try:
            return self.value[key]
        except KeyError:
            return default

    def keys(self):
        """Return object keys."""
        return self.value.keys()

    def values_iter(self):
        """Return object values (renamed to avoid conflict with Node.value)."""
        return self.value.values()

    def items(self):
        """Return object items."""
        return self.value.items()


# Type alias for convenience
Value = Union[
    Null, Bool, Int, Float, DecimalValue, String, Bytes,
    DateTime, Duration, Uuid, Array, Object
]
