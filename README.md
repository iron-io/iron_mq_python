Python language binding for IronMQ. [IronMQ](http://www.iron.io/products/mq) is an elastic message queue for managing data and event flow within cloud applications and between systems. [See How It Works](http://www.iron.io/products/mq/how)

# Getting Started

## Get credentials

To start using iron_mq_python, you need to sign up and get an OAuth2 token.

1. Go to http://iron.io/ and sign up.
2. Get an OAuth2 Token at http://hud.iron.io/tokens

## Install iron_mq_python

```sh
pip install iron_mq_python
```

or just copy `iron_mq.py` and include it in your script:

```python
from iron_mq import *
```

## Configure

```python
ironmq = IronMQ()
```

will try reasonable defaults, accepting following optionally:

```
ironmq = IronMQ(host="mq-aws-us-east-1.iron.io",
                project_id="500f7b....b0f302e9",
                token="Et1En7.....0LuW39Q",
                protocol="https", port=443,
                api_version=1,
                config_file=None)
```

## The Basics

### Listing queues

```python
ironmq.queues()
```
returns list of queues names

we get queue by name:
```python
queue = ironmq.queue("test_queue")
```

### **Push** a message(s) on the queue:

```python
queue.post("Hello world")
```

Message can be described by dict:

```python
message = {
    "body" : "Test Message",
    "timeout" : 120, # Timeout, in seconds. After timeout, item will be placed back on queue. Defaults to 60.
    "delay" : 5, # The item will not be available on the queue until this many seconds have passed. Defaults to 0.
    "expires_in" : 2*24*3600 # How long, in seconds, to keep the item on the queue before it is deleted.
}
queue.post(message)
```

We can post several messages at once:
```python
queue.post("more", "and more", "and more")
queue.post(*[str(i) for i in range(10)])
```

### **Pop** a message off the queue:
```python
queue.get()
```
When you pop/get a message from the queue, it will NOT be deleted.
It will eventually go back onto the queue after a timeout if you don't delete it (default timeout is 60 seconds).
### **Delete** a message from the queue:
```python
queue.delete(message_id)
```
Delete a message from the queue when you're done with it.

### ***Clear*** a queue:
```python
queue.clear()
```

### Get queue ***size***, ***id***, ***total_messages*** and whole ***info***
```python
queue.info()
 # {u'id': u'502d03d3211a8f5e7742d224',
 # u'name': u'queue12',
 # u'reserved': 0,
 # u'size': 15,
 # u'total_messages': 17}
queue.size() # 15
queue.name
queue.total_messages() # 17
queue.id() # u'502d03d3211a8f5e7742d224'
```

# Full Documentation

You can find more documentation here:

* http://iron.io
* http://docs.iron.io
