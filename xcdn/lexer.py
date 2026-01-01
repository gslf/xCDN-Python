"""Tokenizer for xCDN.

The lexer is designed for speed and clear error reporting:
- Ignores whitespace and comments
- Tracks line/column per token
- Recognizes typed string literals: d"...", b"...", u"...", t"...", r"..."
- Supports double-quoted strings and triple-quoted multi-line strings
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum, auto

from .error import Error, ErrorKind, Span, Eof, InvalidToken, Expected, InvalidEscape, InvalidNumber


class TokenType(Enum):
    """Token types."""
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()
    DOLLAR = auto()
    HASH = auto()
    AT = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    IDENT = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    TRIPLE_STRING = auto()
    D_QUOTED = auto()  # decimal d"..."
    B_QUOTED = auto()  # bytes b"..."
    U_QUOTED = auto()  # uuid u"..."
    T_QUOTED = auto()  # datetime t"..."
    R_QUOTED = auto()  # duration r"..."
    EOF = auto()


@dataclass
class Token:
    """A token with its type, optional value, and source position."""
    kind: TokenType
    span: Span
    value: Optional[any] = None


class Lexer:
    """Lexer for xCDN documents."""

    def __init__(self, src: str):
        """Creates a new lexer for the given source string.
        
        Initializes position at (line: 1, col: 1).
        """
        self.src = src
        self.bytes = src.encode('utf-8')
        self.idx = 0
        self.line = 1
        self.col = 1

    def bump(self) -> Optional[int]:
        """Consumes and returns the next byte from the input.
        
        Advances the internal position and updates line/column tracking.
        Returns None if the end of input is reached.
        """
        if self.idx >= len(self.bytes):
            return None
        b = self.bytes[self.idx]
        self.idx += 1
        if b == ord('\n'):
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return b

    def peek(self) -> Optional[int]:
        """Returns the next byte without consuming it.
        
        Returns None if the end of input is reached.
        """
        if self.idx < len(self.bytes):
            return self.bytes[self.idx]
        return None

    def span(self) -> Span:
        """Returns the current span (offset, line, and column)."""
        return Span(offset=self.idx, line=self.line, column=self.col)

    def skip_ws_and_comments(self):
        """Skips whitespace and comments (both line // and block /* */)."""
        while True:
            # whitespace
            while True:
                b = self.peek()
                if b is None:
                    break
                if b in (ord(' '), ord('\t'), ord('\r'), ord('\n')):
                    self.bump()
                    continue
                break

            b = self.peek()
            if b is None:
                return

            if b == ord('/'):
                # comment?
                if self.idx + 1 < len(self.bytes):
                    b2 = self.bytes[self.idx + 1]
                    if b2 == ord('/'):
                        # line comment
                        self.bump()
                        self.bump()
                        while True:
                            c = self.peek()
                            if c is None:
                                break
                            self.bump()
                            if c == ord('\n'):
                                break
                        continue
                    elif b2 == ord('*'):
                        # block comment
                        self.bump()
                        self.bump()
                        while True:
                            c = self.peek()
                            if c is None:
                                break
                            self.bump()
                            if c == ord('*') and self.peek() == ord('/'):
                                self.bump()
                                break
                        continue
            break

    def next_token(self) -> Token:
        """Reads and returns the next token from the source.
        
        Raises Error if an invalid token, malformed number,
        or unterminated string is encountered.
        """
        self.skip_ws_and_comments()
        start = self.span()

        b = self.peek()
        if b is None:
            return Token(kind=TokenType.EOF, span=start)

        # Triple string management
        if self.idx + 2 < len(self.bytes) and self.bytes[self.idx:self.idx+3] == b'"""':
            s = self.read_string(triple=True)
            return Token(kind=TokenType.TRIPLE_STRING, span=start, value=s)

        # Single char tokens
        single_chars = {
            ord('{'): TokenType.LBRACE,
            ord('}'): TokenType.RBRACE,
            ord('['): TokenType.LBRACKET,
            ord(']'): TokenType.RBRACKET,
            ord('('): TokenType.LPAREN,
            ord(')'): TokenType.RPAREN,
            ord(':'): TokenType.COLON,
            ord(','): TokenType.COMMA,
            ord('$'): TokenType.DOLLAR,
            ord('#'): TokenType.HASH,
            ord('@'): TokenType.AT,
        }

        if b in single_chars:
            self.bump()
            return Token(kind=single_chars[b], span=start)

        if b == ord('"'):
            s = self.read_string(triple=False)
            return Token(kind=TokenType.STRING, span=start, value=s)

        # Numbers
        if b in (ord('.'), ord('-'), ord('+')) or (ord('0') <= b <= ord('9')):
            int_opt, float_opt = self.read_number()
            if int_opt is not None:
                return Token(kind=TokenType.INT, span=start, value=int_opt)
            elif float_opt is not None:
                return Token(kind=TokenType.FLOAT, span=start, value=float_opt)
            else:
                raise Error.new(InvalidNumber(), start)

        # Typed strings: d"...", b"...", u"...", t"...", r"..."
        if b in (ord('d'), ord('b'), ord('u'), ord('t'), ord('r')):
            ch = b
            if self.idx + 1 < len(self.bytes) and self.bytes[self.idx + 1] == ord('"'):
                self.bump()  # type char
                s = self.read_string(triple=False)
                kind_map = {
                    ord('d'): TokenType.D_QUOTED,
                    ord('b'): TokenType.B_QUOTED,
                    ord('u'): TokenType.U_QUOTED,
                    ord('t'): TokenType.T_QUOTED,
                    ord('r'): TokenType.R_QUOTED,
                }
                return Token(kind=kind_map[ch], span=start, value=s)

        # Identifiers or keywords
        if is_ident_start(b):
            s = self.read_ident()
            if s == "true":
                return Token(kind=TokenType.TRUE, span=start)
            elif s == "false":
                return Token(kind=TokenType.FALSE, span=start)
            elif s == "null":
                return Token(kind=TokenType.NULL, span=start)
            else:
                return Token(kind=TokenType.IDENT, span=start, value=s)

        raise Error.new(InvalidToken("unknown start"), start)

    def read_ident(self) -> str:
        """Reads an identifier or keyword.
        
        Assumes the first character has already been validated with is_ident_start.
        """
        start = self.idx
        self.bump()
        while True:
            b = self.peek()
            if b is None:
                break
            if is_ident_part(b):
                self.bump()
            else:
                break
        return self.src[start:self.idx]

    def read_string(self, triple: bool) -> str:
        """Reads a string, either normal or triple-quoted.
        
        Args:
            triple: If True, reads a triple-quoted string '''...'''
        
        Raises:
            Error if the string is unterminated or contains invalid escape sequences.
        """
        out = []
        start_span = self.span()

        if triple:
            self.bump()
            self.bump()
            self.bump()
            while True:
                if self.idx + 2 < len(self.bytes) and self.bytes[self.idx:self.idx+3] == b'"""':
                    self.bump()
                    self.bump()
                    self.bump()
                    break
                b = self.bump()
                if b is None:
                    raise Error.new(Eof(), start_span)
                out.append(chr(b))
            return ''.join(out)
        else:
            # must start with "
            if self.bump() != ord('"'):
                raise Error.new(Expected(expected='"', found="not a quote"), start_span)
            
            while True:
                b = self.bump()
                if b is None:
                    raise Error.new(Eof(), start_span)
                
                if b == ord('"'):
                    break
                elif b == ord('\\'):
                    # escape: keep literals as-is for normal strings
                    e = self.bump()
                    if e is None:
                        raise Error.new(InvalidEscape(), start_span)
                    
                    if e == ord('"'):
                        out.append('"')
                    elif e == ord('\\'):
                        out.append('\\')
                    elif e == ord('/'):
                        out.append('\\')
                        out.append('/')
                    elif e == ord('b'):
                        out.append('\\')
                        out.append('b')
                    elif e == ord('f'):
                        out.append('\\')
                        out.append('f')
                    elif e == ord('n'):
                        out.append('\\')
                        out.append('n')
                    elif e == ord('r'):
                        out.append('\\')
                        out.append('r')
                    elif e == ord('t'):
                        out.append('\\')
                        out.append('t')
                    elif e == ord('u'):
                        # keep \uXXXX literally
                        out.append('\\')
                        out.append('u')
                        # append exactly 4 hex digits if present
                        for _ in range(4):
                            h = self.bump()
                            if h is None:
                                raise Error.new(InvalidEscape(), start_span)
                            ch = chr(h)
                            if ch in '0123456789abcdefABCDEF':
                                out.append(ch)
                            else:
                                raise Error.new(InvalidEscape(), start_span)
                    else:
                        raise Error.new(InvalidEscape(), start_span)
                else:
                    out.append(chr(b))
            
            return ''.join(out)

    def read_number(self) -> Tuple[Optional[int], Optional[float]]:
        """Reads a number, which can be an integer or floating point.
        
        Supports optional signs, decimal points, and exponents (scientific notation).
        
        Returns:
            A tuple (Optional[int], Optional[float]) where one of the two values is Some.
        
        Raises:
            Error if the number is malformed.
        """
        start = self.idx
        # optional sign
        if self.peek() in (ord('+'), ord('-')):
            self.bump()
        
        has_dot = False
        has_exp = False
        has_digit = False

        while True:
            b = self.peek()
            if b is None:
                break
            
            if ord('0') <= b <= ord('9'):
                has_digit = True
                self.bump()
            elif b == ord('.') and not has_dot and not has_exp:
                has_dot = True
                self.bump()
            elif b in (ord('e'), ord('E')) and not has_exp:
                has_exp = True
                self.bump()
                if self.peek() in (ord('+'), ord('-')):
                    self.bump()
            else:
                break

        s = self.src[start:self.idx]
        if not has_digit:
            raise Error.new(InvalidNumber(), self.span())
        
        if has_dot or has_exp:
            try:
                x = float(s)
                return (None, x)
            except ValueError:
                raise Error.new(InvalidNumber(), self.span())
        else:
            try:
                i = int(s)
                return (i, None)
            except ValueError:
                raise Error.new(InvalidNumber(), self.span())


def is_ident_start(b: int) -> bool:
    """Checks if a byte can be the start of an identifier.
    
    Identifiers start with A-Z, a-z, or _.
    """
    return (ord('A') <= b <= ord('Z')) or (ord('a') <= b <= ord('z')) or b == ord('_')


def is_ident_part(b: int) -> bool:
    """Checks if a byte can be part of an identifier.
    
    Identifiers can contain A-Z, a-z, 0-9, _, or -.
    """
    return is_ident_start(b) or (ord('0') <= b <= ord('9')) or b == ord('-')
