"""Error types with spans and pretty display."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Span:
    """Location information for diagnostics."""
    offset: int
    line: int
    column: int

    @staticmethod
    def start() -> 'Span':
        return Span(offset=0, line=1, column=1)

    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}"


class ErrorKind(Exception):
    """Base class for parser/lexer errors."""
    pass


class Eof(ErrorKind):
    """Unexpected end of input."""
    def __init__(self):
        super().__init__("unexpected end of input")


class InvalidToken(ErrorKind):
    """Invalid token."""
    def __init__(self, msg: str):
        super().__init__(f"invalid token: {msg}")


class Expected(ErrorKind):
    """Expected something, found something else."""
    def __init__(self, expected: str, found: str):
        super().__init__(f"expected {expected}, found {found}")
        self.expected = expected
        self.found = found


class InvalidEscape(ErrorKind):
    """Invalid escape sequence."""
    def __init__(self):
        super().__init__("invalid escape sequence")


class InvalidNumber(ErrorKind):
    """Invalid number literal."""
    def __init__(self):
        super().__init__("invalid number literal")


class InvalidDecimal(ErrorKind):
    """Invalid decimal literal."""
    def __init__(self, value: str):
        super().__init__(f"invalid decimal literal: {value}")
        self.value = value


class InvalidDateTime(ErrorKind):
    """Invalid RFC3339 datetime."""
    def __init__(self, value: str):
        super().__init__(f"invalid RFC3339 datetime: {value}")
        self.value = value


class InvalidDuration(ErrorKind):
    """Invalid ISO8601 duration."""
    def __init__(self, value: str):
        super().__init__(f"invalid ISO8601 duration: {value}")
        self.value = value


class InvalidUuid(ErrorKind):
    """Invalid UUID."""
    def __init__(self, value: str):
        super().__init__(f"invalid UUID: {value}")
        self.value = value


class Message(ErrorKind):
    """Generic error message."""
    def __init__(self, msg: str):
        super().__init__(msg)


class Error(Exception):
    """Full error with position."""
    def __init__(self, kind: ErrorKind, span: Span, context: Optional[str] = None):
        self.kind = kind
        self.span = span
        self.context = context
        super().__init__(f"{kind} at {span}")

    @staticmethod
    def new(kind: ErrorKind, span: Span) -> 'Error':
        return Error(kind, span)

    @staticmethod
    def with_ctx(kind: ErrorKind, span: Span, ctx: str) -> 'Error':
        return Error(kind, span, ctx)
