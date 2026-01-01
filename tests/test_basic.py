"""Basic integration tests for xCDN."""

from xcdn import parse_str, ser


def test_parse_and_roundtrip_quick_taste():
    """Test parsing and serialization roundtrip."""
    input_text = """
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
  icon: @mime("image/png") b"aGVsbG8=",
}
"""

    doc = parse_str(input_text)
    assert len(doc.values) > 0
    s = ser.to_string_pretty(doc)
    assert "server_config" in s
