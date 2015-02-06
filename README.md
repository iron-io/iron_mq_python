Python language binding for IronMQ. [IronMQ](http://www.iron.io/mq) is an elastic message queue for managing data and event flow within cloud applications and between systems. [See How It Works](http://www.iron.io/mq/how-it-works)

# Getting Started

## Get credentials

To start using iron_mq_python, you need to sign up and get an OAuth2 token.

1. Go to http://iron.io/ and sign up.
2. Get an OAuth2 Token at http://hud.iron.io/tokens

## Install iron_mq_python

```sh
pip install iron-mq
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
queue.get(max=10, timeout=None) # {"messages": [{'id': '..', 'body': '..'}, ..]}
```
Set max to the number of messages to return, 1 by default. An optional `timeout` parameter can be used to specify a per-message timeout, or the timeout the message was posted with will be used.

When you pop/get a message from the queue, it will NOT be deleted.
It will eventually go back onto the queue after a timeout if you don't delete it (default timeout is 60 seconds).

### Get message by id
```python
queue.get_message_by_id("xxxxxxxx")
```

### **Delete** a message from the queue:
```python
queue.delete(message_id)
```
Delete a message from the queue when you're done with it.

Delete multiple messages in one API call:

```python
queue.delete_multiple("xxxxxxxxx", "xxxxxxxxx")
```
Delete multiple messages specified by messages id array.

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

### Peek at messages
To view messages without reserving them, use peek:

```python
msgs = queue.peek(max=10) # {"messages": [{'id': '..', 'body': '..'}, ..]}
```

### Touch a message

To extend the reservation on a reserved message, use touch. The message reservation will be extended by the message's `timeout`.

```python
queue.touch(msg_id)
```

### Release a reserved message
To release a message that is currently reserved, use release:

```python
queue.release(msg_id, delay=30) # message will be released after delay seconds, 0 by defaults
```

### Delete a queue

To delete a queue, use `delete_queue`:

```python
queue.delete_queue()
```

## Push Queues

### Update Queue Information

To update the queue's push type and subscribers, use update:

```python
queue.update(subscribers=["http://endpoint1.com", "https://end.point.com/2"], push_type"unicast")
```

### Add subscribers to a push queue

```python
queue.add_subscribers(*["http://endpoint1.com", "https://end.point.com/2"])
```

### Remove subscribers from a push queue

```python
queue.remove_subscribers(*["http://endpoint1.com", "https://end.point.com/2"])
```

### Get the push statuses of a message

```python
queue.get_message_push_statuses(message_id) # {"subscribers": [{"retries_delay": 60, "retries_remaining": 2, "status_code": 200, "status": "deleted", "url": "http://endpoint1.com", "id": "52.."}, {..}, ..]}
```

### Delete a pushed message

If you respond with a 202 status code, the pushed message will be reserved, not deleted, and should be manually deleted. You can get the message ID and subscriber ID from the push message's headers.

```python
queue.delete_message_push_status(message_id, subscriber_id)
```

## Pull queues

### Add alerts to a queue

```python
fixed_desc_alert = {'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'q'}
progressive_asc_alert = {'type': 'progressive', 'direction': 'asc', 'trigger': 10000, 'queue': 'q'}
queue.add_alerts(*[fixed_desc_alert, progressive_asc_alert])
```

### Update alerts in a queue

```python
progressive_asc_alert = {'type': 'progressive', 'direction': 'asc', 'trigger': 5000, 'queue': 'q'}
queue.update_alerts(*[progressive_asc_alert])
```

### Remove alerts from a queue

```python
q.remove_alerts(*['5305d3b5a3e920763013c796', '513015d32b5a3e763013c796'])
```

### Remove single alert from a queue

```python
q.remove_alert('5305d3b5a3e920763013c796')
```

# Full Documentation

You can find more documentation here:

* http://iron.io
* http://dev.iron.io
