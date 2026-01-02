import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from xcdn import parse_str


def main():
    input_text = """
      config: {
        name: "demo",
        version: "1.0.0",
        ids: [1, 2, 3],
        nested: {
          deep: {
            value: "found it!"
          }
        }
      }
    """
    
    doc = parse_str(input_text)

    if "name" in doc["config"]:
        print("✓ 'name' exists in config")
    
    print("\nConfig keys:")
    for key in doc["config"]:
        print(f"  - {key}")
    
    default_val = doc["config"].get("missing_key", "default_value")
    print(f"\nMissing key with default: {default_val}")
    
    ids_array = doc["config"]["ids"]
    print(f"Array length: {len(ids_array)}")
    print("Array items:")
    for idx, item in enumerate(ids_array):
        print(f"  [{idx}] = {item.value}")

if __name__ == "__main__":
    main()