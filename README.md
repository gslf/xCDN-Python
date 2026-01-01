# > xCDN_ (Python)

A complete Python library to parse, serialize and deserialize **> xCDN_ — eXtensible Cognitive Data Notation**. 

> **What is > xCDN_?**  
> xCDN_ is a human-first, machine-optimized data notation with native types, tags and annotations.
> It supports comments, trailing commas, unquoted keys and multi‑line strings.
> You can read more about this notation in the [> xCDN_ repository](https://github.com/gslf/xCDN).

## Features

- Full streaming document model (one or more top-level values)
- Optional **prolog** (`$schema: "..."`, …)
- Objects, arrays and scalars
- Native types: `Decimal` (`d"..."`), `UUID` (`u"..."`), `DateTime` (`t"..."` RFC3339),
  `Duration` (`r"..."` ISO8601), `Bytes` (`b"..."` Base64)
- `#tags` and `@annotations(args?)` that decorate any value
- Comments: `//` and `/* ... */`
- Trailing commas and unquoted keys
- Pretty or compact serialization

## Example

```xcdn
$schema: "https://gslf.github.io/xCDN/schemas/v1/meta.xcdn",

server_config: {
  host: "localhost",
  // Unquoted keys & trailing commas? Yes.
  ports: [8080, 9090,],

  // Native Decimals & ISO8601 Duration
  timeout: r"PT30S",
  max_cost: d"19.99",

  // Semantic Tagging
  admin: #user {
    id: u"550e8400-e29b-41d4-a716-446655440000",
    role: "superuser"
  },

  // Binary data handling
  icon: @mime("image/png") b"iVBORw0KGgoAAAANSUhEUgAAAAUA...",
}
```

## Usage

```python
from xcdn import parse_str, ser

doc = parse_str(open("sample.xcdn").read())
text = ser.to_string_pretty(doc)
print(text)
```

## Installation

```bash
pip install .
```

Or for development:

```bash
pip install -e .
```

## Testing

```bash
pytest
```

## License

MIT, see [LICENSE](LICENSE).

---

#### This is a :/# GSLF project. 
