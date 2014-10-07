import toml 
from pprint import pprint

with open("test.toml") as f:
    data = f.read()
    print data
    config = toml.loads(data)
    pprint(config, indent=2)
    data2 = toml.dumps(config)
    print data2
    print data == data2


