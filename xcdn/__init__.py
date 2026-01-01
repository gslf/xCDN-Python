"""xCDN - eXtensible Cognitive Data Notation

**xcdn** is a zero-copy, streaming-capable parser/serializer for
**xCDN — eXtensible Cognitive Data Notation**.

The package exposes three public layers:

- `lexer` tokenizes an xCDN document while tracking line/column.
- `parser` produces a typed AST (`ast.Document`) including optional prolog directives.
- `ser` pretty/compact serialization with strong typing (Decimal, UUID, DateTime, Duration, Bytes).

Quick Start
-----------

```python
from xcdn import parse_str, ser

input_text = '''
$schema: "https://gslf.github.io/xCDN/schemas/v1/meta.xcdn",

server_config: {
  host: "localhost",
  ports: [8080, 9090,],
  timeout: r"PT30S",
  max_cost: d"19.99",
  admin: #user { id: u"550e8400-e29b-41d4-a716-446655440000", role: "superuser" },
  icon: @mime("image/png") b"aGVsbG8=",
}
'''

doc = parse_str(input_text)
assert len(doc.values) >= 1

# Serialize it back
text = ser.to_string_pretty(doc)
print(text)
```

Design notes
------------

* This implementation follows the public xCDN grammar and documentation.
* It supports: comments, unquoted keys, trailing commas, multi-line strings ('''...'''),
  native types (Decimal, UUID, DateTime, Duration, Bytes), `#tags`, and `@annotations`.
* We do not preserve comments/insignificant whitespace on serialization.

See the project repository for the xCDN specification and examples.

Package layout
--------------
- `ast` — core data structures
- `error` — structured error diagnostics with spans
- `lexer` — the tokenizer
- `parser` — recursive-descent parser
- `ser` — serializer
"""

from .parser import parse_str, parse_reader
from . import ast
from . import error
from . import lexer
from . import ser

__version__ = "0.1.0"
__all__ = ["parse_str", "parse_reader", "ast", "error", "lexer", "ser"]
