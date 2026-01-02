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

    name = doc["config"]["name"].value
    print(f"Name: {name}")
    
    version = doc["config"]["version"].value
    print(f"Version: {version}")
    
    first_id = doc["config"]["ids"][0].value
    print(f"First ID: {first_id}")
    
    deep_value = doc["config"]["nested"]["deep"]["value"].value
    print(f"Deep value: {deep_value}")
    
   


if __name__ == "__main__":
    main()
