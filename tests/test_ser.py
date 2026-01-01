"""Serialization tests for xCDN."""

from xcdn import parse_str, ser


def test_serialize_roundtrip_pretty_and_compact():
    """Test pretty and compact serialization."""
    input_text = """
$schema: "https://gslf.github.io/xCDN/schemas/v1/meta.xcdn",

config: {
  host: "localhost",
  ports: [8080, 9090,],
  timeout: r"PT30S",
  cost: d"19.99",
  admin: #user { id: u"550e8400-e29b-41d4-a716-446655440000", role: "super" },
  icon: @mime("image/png") b"aGVsbG8=",
}
"""
    doc = parse_str(input_text)
    pretty = ser.to_string_pretty(doc)
    compact = ser.to_string_compact(doc)
    assert "config" in pretty
    assert "config" in compact
    assert '\n' not in compact or compact.count('\n') < pretty.count('\n')


def test_serialize_trailing_commas_option():
    """Test trailing commas option."""
    input_text = "{ a: 1, b: 2, }"
    doc = parse_str(input_text)
    s = ser.to_string_with_format(doc, ser.Format(pretty=True, indent=2, trailing_commas=False))
    assert "a: " in s
    # Should not have trailing comma before closing brace
    assert not s.rstrip().endswith(",\n}")


def test_serialize_strings_and_escapes():
    """Test string serialization with escapes."""
    input_text = r'{ a: "line\n", b: "quote: \"", c: "slash: \\", d: "control: \u0001" }'
    doc = parse_str(input_text)
    s = ser.to_string_pretty(doc)
    assert "\\n" in s
    assert '\\"' in s
    assert "\\\\" in s
