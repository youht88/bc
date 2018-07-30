import asyncio
from kademlia.network import Server

# Create a node and start listening on port 5678
node = Server()
node.listen(8468)

# Bootstrap the node by connecting to other known nodes, in this case
# replace 123.123.123.123 with the IP of another node and optionally
# give as many ip/port combos as you can for other nodes.
loop = asyncio.get_event_loop()
loop.run_until_complete(node.bootstrap([("192.168.31.124", 8468)]))

# set a value for the key "my-key" on the network
loop.run_until_complete(node.set("my-key", "my awesome value"))

# get the value associated with "my-key" from the network
result = loop.run_until_complete(node.get("my-key"))
print(result)