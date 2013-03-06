IronMQ Python Client Library
-------------

Python language binding for IronMQ. [IronMQ](http://www.iron.io/products/mq) is an elastic message queue for managing data and event flow within cloud applications and between systems. [See How It Works](http://www.iron.io/products/mq/how)

# Getting Started

1\. Install iron_mq_python

```sh
pip install iron-mq
```

or just copy `iron_mq.py` and include it in your script:

```python
from iron_mq import *
```

2. Setup your Iron.io credentials: http://dev.iron.io/mq/reference/configuration/

3\. Create an IronMQ client object:

```python
ironmq = IronMQ(project_id='500f7b....b0f302e9', token='Et1En7.....0LuW39Q')
```

# The Basics

### Get Queues List

```python
queues = ironmq.queues()
```

returns list of `Queue` objects.

### Get a Queue Object

You can have as many queues as you want, each with their own unique set of messages.

```python
queue = ironmq.queue('my_queue')
```

Now you can use it.

### Post a Message on a Queue

Messages are placed on the queue in a FIFO arrangement.
If a queue does not exist, it will be created upon the first posting of a message.

```python
queue.post('hello world!')
```

### Retrieve Queue Information

```python
q_info = queue.info()

q_id = queue.id()
q_size = queue.size()
q_name = queue.name
```

### Get a Message off a Queue

```python
msg = queue.get()

data = msg.body
```

When you pop/get a message from the queue, it is no longer on the queue but it still exists within the system.
You have to explicitly delete the message or else it will go back onto the queue after the `timeout`.
The default `timeout` is 60 seconds. Minimal `timeout` is 30 seconds.

### Delete a Message from a Queue

```python
msg.delete()
```

Be sure to delete a message from the queue when you're done with it.


# IronMQ

`IronMQ` class uses `IronClient` from [iron_core_python](https://github.com/iron-io/iron_core_python) and provides easy access to the queues.

```python
ironmq = IronMQ(config='config.ini')
# or
ironmq = IronMQ(project_id='PROJECT_ID', token='TOKEN')
```

### List Queues

```python
queues = ironmq.queues()
```

**Optional parameters:**

* `page`: The 0-based page to view. The default is 0.
* `per_page`: The number of queues to return per page. The default is 30, the maximum is 100.

```python
queues = ironmq.queues(page=2, per_page=5)
```

### Get Queue by Name

```python
queue = ironmq.queue('my_queue')
```

**Note:** if queue with desired name does not exist it returns fake queue.
Queue will be created automatically on post of first message or queue configuration update.

# Queues

### Retrieve Queue Information

```python
info = queue.info() # {'id': '5127bf043264140e863e2283', 'name': 'my_queue', ...}

q_id = queue.id() # "5127bf043264140e863e2283"
# Does queue exists on server? Alias for `queue.id is None`
is_new = queue.is_new() # False

size = queue.size() # 7
name = queue.name # 'my_queue'
overall_messages = queue.total_messages() # 13
subscribers = queue.subscribers() # [Subscription, ...]

push_type = queue.push_type() # 'multicast'
# Does queue Push Queue? Alias for `queue.push_type is not None`
is_push_queue = queue.is_push_queue() # True
```

**Warning:** to be sure configuration information is up-to-date
client library call IronMQ API each time you request for any parameter except `queue.name`.
In this case you may prefer to use `queue.info()` to have `dict` with all available info parameters.

### Delete a Message Queue

```python
queue.delete() # True
```

### Post Messages to a Queue

**Single message:**

```python
queue.post('something helpful', timeout=300)
# or
queue.post({'message_key1': 'value1', 'number': 300}, timeout=300)
```

**Multiple messages:**
```python
messages = [{'key1': 'first', 'key2': 300}, 'second', {'number': 'third'}]

queue.post(messages, expires_in=424242)
```

**Optional parameters for messages:**

* `timeout`: After timeout (in seconds), item will be placed back onto queue.
You must delete the message from the queue to ensure it does not go back onto the queue.
 Default is 60 seconds. Minimum is 30 seconds. Maximum is 86,400 seconds (24 hours).

* `delay`: The item will not be available on the queue until this many seconds have passed.
Default is 0 seconds. Maximum is 604,800 seconds (7 days).

* `expires_in`: How long in seconds to keep the item on the queue before it is deleted.
Default is 604,800 seconds (7 days). Maximum is 2,592,000 seconds (30 days).

### Get Messages from a Queue

```python
message = queue.get() # Message

# or N messages
messages = queue.get(count=7, timeout=300) # [Message, ...]
```

**Optional parameters:**

* `count`: The maximum number of messages to get. Default is 1. Maximum is 100.

* `timeout`: timeout: After timeout (in seconds), item will be placed back onto queue.
You must delete the message from the queue to ensure it does not go back onto the queue.
If not set, value from POST is used. Default is 60 seconds. Minimum is 30 seconds.
Maximum is 86,400 seconds (24 hours).

When `count` parameter is specified and greater than 1 method returns `Array` of `Queue`s.
Otherwise, `Queue` object would be returned.

### Touch a Message on a Queue

Touching a reserved message extends its timeout by the duration specified when the message was created, which is 60 seconds by default.

```python
message = queue.get() # Message

message.touch()
```

### Release Message

```python
message = queue.get() # Message

message.release() # True
# or
message.release(delay=42) # True
```

**Optional parameters:**

* `delay`: The item will not be available on the queue until this many seconds have passed.
Default is 0 seconds. Maximum is 604,800 seconds (7 days).

### Delete a Message from a Queue

```python
message = queue.get()

message.delete() # True
```

### Peek Messages from a Queue

Peeking at a queue returns the next messages on the queue, but it does not reserve them.

```python
message = queue.peek() # Message
# or multiple messages
messages = queue.peek(count=13) # [Message, ...]
```

**Optional parameters:**

* `count`: The maximum number of messages to peek. Default is 1. Maximum is 100.

### Clear a Queue

```ruby
queue.clear() # True
```

# Push Queues

IronMQ push queues allow you to setup a queue that will push to an endpoint, rather than having to poll the endpoint. 
[Here's the announcement for an overview](http://blog.iron.io/2013/01/ironmq-push-queues-reliable-message.html). 

### Update a Message Queue

```python
queue.update(
    subscribers=[
        'http://endpoint.com/first',
        'http://endpoint.com/second'
    ],
    push_type='multicast',
    retries=5,
    retries_delay=120
)
```

**The following parameters are all related to Push Queues:**

* `subscribers`: An array of subscribers dicts containing a “url” field.
This set of subscribers will replace the existing subscribers.
To add or remove subscribers, see the add subscribers endpoint or the remove subscribers endpoint.
See below for example json.
* `push_type`: Either `'multicast'` to push to all subscribers or `'unicast'` to push to one and only one subscriber. Default is `multicast`.
* `retries`: How many times to retry on failure. Default is 3.
* `retries_delay`: Delay between each retry in seconds. Default is 60.

### Set Subscribers on a Queue

Subscribers can be any HTTP endpoint. `push_type` is one of:

* `multicast`: will push to all endpoints/subscribers
* `unicast`: will push to one and only one endpoint/subscriber

```python
ptype = 'multicast'
subscribers = [
    'http://rest-test.iron.io/code/200?store=key1',
    'http://rest-test.iron.io/code/200?store=key2'
]

queue.update(subscribers=subscribers, push_type=ptype)
```

### Add/Remove Subscribers on a Queue

```python
queue.subscribe('http://nowhere.com')

queue.subscribe([
    'http://first.endpoint.com/process',
    {'http://second.endpoint.com/process'
])

queue.unsubscribe('http://nowhere.com')

queue.unsubscribe([
    'http://first.endpoint.com/process',
    'http://second.endpoint.com/process'
])
```

### Get Message Push Status

After pushing a message:

```python
subscriptions = queue.get(message.id).push_status()
```

Returns an array of subscribers with status.

### Delete Message Push Status

```python
subscriptions = queue.get(msg.id).push_status()

for subscription in subscriptions:
    subscription.delete()
```


-------------
© 2011 - 2013 Iron.io Inc. All Rights Reserved.
