"""Parser tests for xCDN."""

from xcdn.ast import String, Int, Bool, Object, Array
from xcdn.error import Expected
from xcdn import parse_str


def test_parse_prolog_collects_directives():
    """Test parsing prolog directives."""
    input_text = """
$schema: "https://example.com/schema",
$version: 2,

{ answer: 42 }
"""

    doc = parse_str(input_text)
    assert len(doc.prolog) == 2
    assert doc.prolog[0].name == "schema"
    assert isinstance(doc.prolog[0].value, String)
    assert doc.prolog[0].value.value == "https://example.com/schema"
    assert isinstance(doc.prolog[1].value, Int)
    assert doc.prolog[1].value.value == 2
    assert isinstance(doc.values[0].value, Object)
    obj = doc.values[0].value
    answer = obj.value["answer"]
    assert isinstance(answer.value, Int)
    assert answer.value.value == 42


def test_parse_implicit_top_level_object():
    """Test parsing implicit top-level object."""
    input_text = """
name: "xcdn",
nested: { flag: true },
"""

    doc = parse_str(input_text)
    assert len(doc.values) == 1
    root = doc.values[0]
    assert isinstance(root.value, Object)
    obj = root.value
    name = obj.value["name"]
    assert isinstance(name.value, String)
    nested = obj.value["nested"]
    assert isinstance(nested.value, Object)
    flag = nested.value.value["flag"]
    assert isinstance(flag.value, Bool)
    assert flag.value.value is True


def test_parse_annotations_and_tags():
    """Test parsing annotations and tags."""
    input_text = '@mime("image/png") #thumbnail b"aGVsbG8="'

    doc = parse_str(input_text)
    assert len(doc.values) == 1
    node = doc.values[0]
    assert len(node.annotations) == 1
    assert len(node.tags) == 1
    annotation = node.annotations[0]
    assert annotation.name == "mime"
    assert len(annotation.args) == 1
    assert isinstance(annotation.args[0], String)
    assert annotation.args[0].value == "image/png"
    assert node.tags[0].name == "thumbnail"


def test_parse_stream_of_values():
    """Test parsing stream of values."""
    input_text = "{ a: 1 }\n42\n"
    doc = parse_str(input_text)
    assert len(doc.values) == 2
    assert isinstance(doc.values[0].value, Object)
    assert isinstance(doc.values[1].value, Int)
    assert doc.values[1].value.value == 42


def test_parse_reports_missing_colon():
    """Test that parser detects missing colon."""
    input_text = "{ a 1 }"
    try:
        parse_str(input_text)
        assert False, "Should have raised an error"
    except Exception as e:
        assert isinstance(e.kind, Expected)
