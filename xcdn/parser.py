"""Recursive-descent parser for xCDN.

It implements the published grammar shape:
- Optional prolog: `$ident : value` entries separated by commas
- One or more values (streaming)
- Values: object, array, string/number/bool/null, and typed literals
- Decorations: zero or more `@annotation(args?)` and `#tag` preceding any value
"""

from typing import Optional, IO
from decimal import Decimal
from datetime import datetime
from uuid import UUID
import base64

from .ast import (
    Annotation, Directive, Document, Node, Tag,
    Null, Bool, Int, Float, DecimalValue, String, Bytes,
    DateTime, Duration, Uuid, Array, Object
)
from .error import Error, ErrorKind, Span, Expected, Message, InvalidDecimal, InvalidUuid, InvalidDateTime, InvalidDuration
from .lexer import Lexer, Token, TokenType


def parse_str(src: str) -> Document:
    """Parse a full xCDN document from a string."""
    p = Parser(src)
    return p.parse_document()


def parse_reader(reader: IO[str]) -> Document:
    """Parse a full xCDN document from any reader (UTF-8)."""
    s = reader.read()
    return parse_str(s)


class Parser:
    """Recursive-descent parser for xCDN documents."""

    def __init__(self, src: str):
        self.lex = Lexer(src)
        self.look: Optional[Token] = None

    def bump(self) -> Token:
        """Consume and return the next token."""
        if self.look is not None:
            t = self.look
            self.look = None
            return t
        return self.lex.next_token()

    def peek(self) -> Token:
        """Peek at the next token without consuming it."""
        if self.look is None:
            self.look = self.lex.next_token()
        return self.look

    def expect(self, kind: TokenType, expected: str) -> Token:
        """Expect a specific token type."""
        t = self.bump()
        if t.kind == kind:
            return t
        else:
            raise Error.new(Expected(expected=expected, found=token_name(t.kind)), t.span)

    def parse_document(self) -> Document:
        """Parse a complete xCDN document."""
        doc = Document.new()

        # Optional prolog: sequence of `$ident : value` separated by commas
        while True:
            if self.peek().kind == TokenType.DOLLAR:
                self.bump()  # consume $
                name = self.parse_ident_string()
                self.expect(TokenType.COLON, ":")
                value_node = self.parse_node()
                doc.prolog.append(Directive(name=name, value=value_node.value))
                # optional comma
                if self.peek().kind == TokenType.COMMA:
                    self.bump()
            else:
                break

        # After prolog, allow either:
        # - a single top-level implicit object (YAML-style without outer braces)
        # - or a stream of values

        # Detect implicit top-level object: starts with a key (Ident or String) followed by ':'
        peek_kind = self.peek().kind
        if peek_kind in (TokenType.IDENT, TokenType.STRING):
            # consume key and ensure ':' follows; then parse as implicit object until EOF
            first_key = self.parse_key()
            self.expect(TokenType.COLON, ":")
            obj_map = {}
            # value for the first key supports decorations via parse_node
            first_node = self.parse_node()
            obj_map[first_key] = first_node

            # subsequent entries until EOF
            while True:
                peek_kind = self.peek().kind
                if peek_kind == TokenType.COMMA:
                    self.bump()  # optional comma, allow trailing
                elif peek_kind in (TokenType.IDENT, TokenType.STRING):
                    key = self.parse_key()
                    self.expect(TokenType.COLON, ":")
                    node = self.parse_node()
                    obj_map[key] = node
                elif peek_kind == TokenType.EOF:
                    break
                else:
                    # anything else terminates the implicit object
                    tname = token_name(peek_kind)
                    t = self.bump()
                    raise Error.new(Expected(expected="object key, ", found=tname), t.span)

            doc.values.append(Node(annotations=[], tags=[], value=Object(value=obj_map)))
        elif peek_kind == TokenType.EOF:
            return doc
        else:
            # 0..* values (streams)
            first = self.parse_node()
            doc.values.append(first)
            while True:
                if self.peek().kind == TokenType.EOF:
                    break
                else:
                    n = self.parse_node()
                    doc.values.append(n)

        return doc

    def parse_node(self) -> Node:
        """Parse a node with optional decorations (tags and annotations)."""
        # Gather decorations
        annotations = []
        tags = []
        while True:
            peek_kind = self.peek().kind
            if peek_kind == TokenType.AT:
                self.bump()
                name = self.parse_ident_string()
                # optional arg list: (arg1, arg2, ...)
                args = []
                if self.peek().kind == TokenType.LPAREN:
                    self.bump()  # (
                    if self.peek().kind == TokenType.RPAREN:
                        self.bump()  # )
                    else:
                        while True:
                            v = self.parse_value()
                            args.append(v)
                            if self.peek().kind == TokenType.COMMA:
                                self.bump()
                                continue
                            elif self.peek().kind == TokenType.RPAREN:
                                self.bump()
                                break
                            else:
                                t = self.bump()
                                raise Error.new(Expected(expected='","or ")"', found=token_name(t.kind)), t.span)
                annotations.append(Annotation(name=name, args=args))
            elif peek_kind == TokenType.HASH:
                self.bump()
                name = self.parse_ident_string()
                tags.append(Tag(name=name))
            else:
                break

        v = self.parse_value()
        return Node(annotations=annotations, tags=tags, value=v)

    def parse_ident_string(self) -> str:
        """Parse an identifier."""
        t = self.bump()
        if t.kind == TokenType.IDENT:
            return t.value
        else:
            raise Error.new(Expected(expected="identifier", found=token_name(t.kind)), t.span)

    def parse_key(self) -> str:
        """Parse an object key (identifier or string)."""
        t = self.bump()
        if t.kind == TokenType.IDENT:
            return t.value
        elif t.kind == TokenType.STRING:
            return t.value
        else:
            raise Error.new(Expected(expected="object key", found=token_name(t.kind)), t.span)

    def parse_value(self):
        """Parse a value."""
        t = self.bump()

        if t.kind == TokenType.LBRACE:
            return self.parse_object()
        elif t.kind == TokenType.LBRACKET:
            return self.parse_array()
        elif t.kind in (TokenType.STRING, TokenType.TRIPLE_STRING):
            return String(value=t.value)
        elif t.kind == TokenType.TRUE:
            return Bool(value=True)
        elif t.kind == TokenType.FALSE:
            return Bool(value=False)
        elif t.kind == TokenType.NULL:
            return Null()
        elif t.kind == TokenType.INT:
            return Int(value=t.value)
        elif t.kind == TokenType.FLOAT:
            return Float(value=t.value)
        elif t.kind == TokenType.D_QUOTED:
            try:
                d = Decimal(t.value)
                return DecimalValue(value=d)
            except Exception:
                raise Error.new(InvalidDecimal(t.value), t.span)
        elif t.kind == TokenType.B_QUOTED:
            # try standard Base64 first, then URL-safe without padding
            try:
                decoded = base64.b64decode(t.value)
            except Exception:
                try:
                    decoded = base64.urlsafe_b64decode(t.value)
                except Exception as e:
                    raise Error.with_ctx(Message(str(e)), t.span, "invalid base64")
            return Bytes(value=decoded)
        elif t.kind == TokenType.U_QUOTED:
            try:
                u = UUID(t.value)
                return Uuid(value=u)
            except Exception:
                raise Error.new(InvalidUuid(t.value), t.span)
        elif t.kind == TokenType.T_QUOTED:
            try:
                dt = datetime.fromisoformat(t.value.replace('Z', '+00:00'))
                return DateTime(value=dt)
            except Exception as e:
                raise Error.with_ctx(InvalidDateTime(t.value), t.span, str(e))
        elif t.kind == TokenType.R_QUOTED:
            # For simplicity, we store ISO8601 duration as a string
            # A proper implementation would parse it into a structure
            return Duration(value=t.value)
        else:
            raise Error.new(Expected(expected="value", found=token_name(t.kind)), t.span)

    def parse_object(self):
        """Parse an object."""
        obj_map = {}
        # zero or more entries
        while True:
            if self.peek().kind == TokenType.RBRACE:
                self.bump()
                break
            else:
                key = self.parse_key()
                self.expect(TokenType.COLON, ":")
                node = self.parse_node()
                obj_map[key] = node
                # optional comma
                if self.peek().kind == TokenType.COMMA:
                    self.bump()  # allow trailing commas
                elif self.peek().kind == TokenType.RBRACE:
                    pass
        return Object(value=obj_map)

    def parse_array(self):
        """Parse an array."""
        items = []
        while True:
            if self.peek().kind == TokenType.RBRACKET:
                self.bump()
                break
            else:
                node = self.parse_node()
                items.append(node)
                # optional comma
                if self.peek().kind == TokenType.COMMA:
                    self.bump()
        return Array(value=items)


def token_name(k: TokenType) -> str:
    """Get a human-readable name for a token type."""
    names = {
        TokenType.LBRACE: "{",
        TokenType.RBRACE: "}",
        TokenType.LBRACKET: "[",
        TokenType.RBRACKET: "]",
        TokenType.LPAREN: "(",
        TokenType.RPAREN: ")",
        TokenType.COLON: ":",
        TokenType.COMMA: ",",
        TokenType.DOLLAR: "$",
        TokenType.HASH: "#",
        TokenType.AT: "@",
        TokenType.TRUE: "true",
        TokenType.FALSE: "false",
        TokenType.NULL: "null",
        TokenType.IDENT: "identifier",
        TokenType.INT: "integer",
        TokenType.FLOAT: "float",
        TokenType.STRING: "string",
        TokenType.TRIPLE_STRING: '"""string"""',
        TokenType.D_QUOTED: 'd"..."',
        TokenType.B_QUOTED: 'b"..."',
        TokenType.U_QUOTED: 'u"..."',
        TokenType.T_QUOTED: 't"..."',
        TokenType.R_QUOTED: 'r"..."',
        TokenType.EOF: "EOF",
    }
    return names.get(k, str(k))
