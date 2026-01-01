"""Lexer tests for xCDN."""

from xcdn.lexer import Lexer, TokenType
from xcdn.error import InvalidNumber


def test_lex_basic_symbols():
    """Test lexing basic symbols."""
    lx = Lexer("{ } [ ] ( ) : , $ # @")
    kinds = [
        TokenType.LBRACE, TokenType.RBRACE,
        TokenType.LBRACKET, TokenType.RBRACKET,
        TokenType.LPAREN, TokenType.RPAREN,
        TokenType.COLON, TokenType.COMMA,
        TokenType.DOLLAR, TokenType.HASH, TokenType.AT,
        TokenType.EOF,
    ]
    for expect in kinds:
        t = lx.next_token()
        assert t.kind == expect


def test_lex_ident_and_keywords():
    """Test lexing identifiers and keywords."""
    lx = Lexer("true false null ident_1 another-ident")
    t1 = lx.next_token()
    assert t1.kind == TokenType.TRUE
    t2 = lx.next_token()
    assert t2.kind == TokenType.FALSE
    t3 = lx.next_token()
    assert t3.kind == TokenType.NULL
    t4 = lx.next_token()
    assert t4.kind == TokenType.IDENT and t4.value == "ident_1"
    t5 = lx.next_token()
    assert t5.kind == TokenType.IDENT and t5.value == "another-ident"


def test_lex_numbers_int_float_exp():
    """Test lexing numbers."""
    lx = Lexer("0 -42 3.14 1e10 -2.5E-3 +7")
    assert lx.next_token().kind == TokenType.INT
    assert lx.next_token().kind == TokenType.INT
    assert lx.next_token().kind == TokenType.FLOAT
    assert lx.next_token().kind == TokenType.FLOAT
    assert lx.next_token().kind == TokenType.FLOAT
    assert lx.next_token().kind == TokenType.INT


def test_lex_strings_and_triple():
    """Test lexing strings."""
    lx = Lexer('"hi\\n" """multi\nline""" ')
    t1 = lx.next_token()
    assert t1.kind == TokenType.STRING and t1.value == "hi\\n"
    t2 = lx.next_token()
    assert t2.kind == TokenType.TRIPLE_STRING and "multi\nline" in t2.value


def test_lex_typed_strings():
    """Test lexing typed strings."""
    lx = Lexer('d"19.99" b"aGVsbG8=" u"550e8400-e29b-41d4-a716-446655440000" t"2020-01-01T00:00:00Z" r"PT30S"')
    assert lx.next_token().kind == TokenType.D_QUOTED
    assert lx.next_token().kind == TokenType.B_QUOTED
    assert lx.next_token().kind == TokenType.U_QUOTED
    assert lx.next_token().kind == TokenType.T_QUOTED
    assert lx.next_token().kind == TokenType.R_QUOTED


def test_lex_comments_are_skipped():
    """Test that comments are properly skipped."""
    lx = Lexer("// cmt\n/* block */ ident // tail\n")
    t = lx.next_token()
    assert t.kind == TokenType.IDENT and t.value == "ident"
    assert lx.next_token().kind == TokenType.EOF


def test_lex_invalid_number_error():
    """Test that invalid numbers raise errors."""
    lx = Lexer("-e")
    try:
        lx.next_token()
        assert False, "Should have raised an error"
    except Exception as e:
        assert isinstance(e.kind, InvalidNumber)
