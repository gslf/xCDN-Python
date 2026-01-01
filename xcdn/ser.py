"""Serializer for xCDN.

Provides pretty and compact string encoders and a streaming writer.
"""

from dataclasses import dataclass
import base64

from .ast import (
    Annotation, Document, Node, Tag,
    Null, Bool, Int, Float, DecimalValue, String, Bytes,
    DateTime, Duration, Uuid, Array, Object
)
from .error import Error


@dataclass
class Format:
    """Formatting options for serialization."""
    pretty: bool = True
    indent: int = 2
    trailing_commas: bool = True


def to_string_pretty(doc: Document) -> str:
    """Serialize a Document to a String using Format defaults."""
    return to_string_with_format(doc, Format())


def to_string_compact(doc: Document) -> str:
    """Serialize a Document to a compact String (no extra whitespace)."""
    return to_string_with_format(doc, Format(pretty=False, indent=0, trailing_commas=False))


def to_string_with_format(doc: Document, fmt: Format) -> str:
    """Serialize a Document with custom options."""
    out = []
    first_dir = True
    for d in doc.prolog:
        if not first_dir and fmt.pretty:
            out.append("\n")
        out.append(f"${d.name}: ")
        write_value(out, d.value, fmt, 0)
        if fmt.trailing_commas:
            out.append(',')
        if fmt.pretty:
            out.append("\n")
        first_dir = False

    for i, node in enumerate(doc.values):
        if i > 0 and fmt.pretty:
            out.append("\n")
        write_node(out, node, fmt, 0)
        if i + 1 < len(doc.values) and fmt.pretty:
            out.append("\n")

    return ''.join(out)


def write_node(out: list, node: Node, fmt: Format, depth: int):
    """Write a node with its decorations."""
    for a in node.annotations:
        write_annotation(out, a, fmt)
        out.append(' ')
    for t in node.tags:
        write_tag(out, t, fmt)
        out.append(' ')
    write_value(out, node.value, fmt, depth)


def write_annotation(out: list, a: Annotation, fmt: Format):
    """Write an annotation."""
    out.append('@')
    out.append(a.name)
    if a.args:
        out.append('(')
        for i, v in enumerate(a.args):
            if i > 0:
                out.append(', ')
            write_value(out, v, Format(pretty=False, indent=0, trailing_commas=False), 0)
        out.append(')')


def write_tag(out: list, t: Tag, fmt: Format):
    """Write a tag."""
    out.append('#')
    out.append(t.name)


def write_value(out: list, v, fmt: Format, depth: int):
    """Write a value."""
    if isinstance(v, Null):
        out.append("null")
    elif isinstance(v, Bool):
        out.append("true" if v.value else "false")
    elif isinstance(v, Int):
        out.append(str(v.value))
    elif isinstance(v, Float):
        out.append(str(v.value))
    elif isinstance(v, DecimalValue):
        out.append('d"')
        out.append(str(v.value))
        out.append('"')
    elif isinstance(v, String):
        write_string(out, v.value)
    elif isinstance(v, Bytes):
        out.append('b"')
        out.append(base64.b64encode(v.value).decode('ascii'))
        out.append('"')
    elif isinstance(v, DateTime):
        out.append('t"')
        # Format as RFC3339
        out.append(v.value.isoformat().replace('+00:00', 'Z'))
        out.append('"')
    elif isinstance(v, Duration):
        out.append('r"')
        out.append(v.value)
        out.append('"')
    elif isinstance(v, Uuid):
        out.append('u"')
        out.append(str(v.value))
        out.append('"')
    elif isinstance(v, Array):
        out.append('[')
        if fmt.pretty and v.value:
            out.append('\n')
        for i, n in enumerate(v.value):
            if fmt.pretty:
                indent(out, depth + 1, fmt.indent)
            write_node(out, n, fmt, depth + 1)
            if i + 1 < len(v.value) or fmt.trailing_commas:
                out.append(',')
            if fmt.pretty:
                out.append('\n')
        if fmt.pretty and v.value:
            indent(out, depth, fmt.indent)
        out.append(']')
    elif isinstance(v, Object):
        out.append('{')
        if fmt.pretty and v.value:
            out.append('\n')
        items = list(v.value.items())
        for i, (k, n) in enumerate(items):
            if fmt.pretty:
                indent(out, depth + 1, fmt.indent)
            write_key(out, k)
            out.append(': ')
            write_node(out, n, fmt, depth + 1)
            if i + 1 < len(items) or fmt.trailing_commas:
                out.append(',')
            if fmt.pretty:
                out.append('\n')
        if fmt.pretty and v.value:
            indent(out, depth, fmt.indent)
        out.append('}')


def indent(out: list, depth: int, space: int):
    """Write indentation."""
    out.append(' ' * (depth * space))


def write_key(out: list, k: str):
    """Write an object key."""
    if is_simple_ident(k):
        out.append(k)
    else:
        write_string(out, k)


def is_simple_ident(s: str) -> bool:
    """Check if a string can be written as an unquoted identifier."""
    if not s:
        return False
    
    chars = list(s)
    first = chars[0]
    if first not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_':
        return False
    
    for c in chars[1:]:
        if c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-':
            return False
    
    return True


def write_string(out: list, s: str):
    """Write a string with proper escaping."""
    # Use single-line strings for now; multi-line strings could be used as an optimization.
    out.append('"')
    for ch in s:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\r':
            out.append('\\r')
        elif ch == '\t':
            out.append('\\t')
        elif ord(ch) < 32:  # control character
            out.append(f'\\u{ord(ch):04X}')
        else:
            out.append(ch)
    out.append('"')
