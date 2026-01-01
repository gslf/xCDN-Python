"""Example roundtrip script for xCDN."""

from xcdn import parse_str, ser


def main():
    """Parse and serialize an xCDN document."""
    input_text = """
      $schema: "https://gslf.github.io/xCDN/schemas/v1/meta.xcdn",

      config: {
        name: "demo",
        ids: [1,2,3,],
        timeout: r"PT30S",
        id: u"550e8400-e29b-41d4-a716-446655440000",
        created_at: t"2025-12-07T10:00:00Z",
        payload: b"aGVsbG8=",
      }
    """
    
    doc = parse_str(input_text)
    text = ser.to_string_pretty(doc)
    print(text)


if __name__ == "__main__":
    main()
