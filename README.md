Python language binding for IronMQ. [IronMQ](http://www.iron.io/products/mq) is an elastic message queue for managing data and event flow within cloud applications and between systems. [See How It Works](http://www.iron.io/products/mq/how)

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
ironmq = IronMQ(host='mq-aws-us-east-1.iron.io',
                project_id='500f7b....b0f302e9',
                token='Et1En7.....0LuW39Q',
                protocol='https', port=443,
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
queue = ironmq.queue('test_queue')
```

### **Push** a message(s) on the queue:

```python
queue.post('Hello world')
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
Can no longer set timeout when posting a message, only when reserving one.

We can post several messages at once:
```python
queue.post('more', 'and more', 'and more')
queue.post(*[str(i) for i in range(10)])
```

### Reserve messages
```python
queue.reserve(n=10, timeout=None, wait=0, delete=false)
```
All fields are optional.

- n: The maximum number of messages to get. Default is 1. Maximum is 100. Note: You may not receive all n messages on every request, the more sparse the queue, the less likely you are to receive all n messages.
- timeout:  After timeout (in seconds), item will be placed back onto queue. You must delete the message from the queue to ensure it does not go back onto the queue. If not set, value from queue is used. Default is 60 seconds, minimum is 30 seconds, and maximum is 86,400 seconds (24 hours).
- wait: Time to long poll for messages, in seconds. Max is 30 seconds. Default 0.
- delete: If true, do not put each message back on to the queue after reserving. Default false.

When you reserve a message from the queue, it will NOT be deleted.
It will eventually go back onto the queue after a timeout if you don't delete it (default timeout is 60 seconds).


### Get message by id
```python
queue.get_message_by_id('xxxxxxxx')
```

### **Delete** a message from the queue:
```python
queue.delete(message_id)
```
Delete a message from the queue when you're done with it.
```python
queue.delete(message_id, reservation_id)
```
Reserved message could not be deleted without reservation id.

Delete multiple messages in one API call:

```python
ids = queue.post('more', 'and more', 'and more')['ids']
queue.delete_multiple(ids = ids);
```
Delete multiple messages specified by messages id.

```python
messages = queue.reserve(3)
queue.delete_multiple(messages = messages);
```
Delete multiple messages specified by response after reserving messages. 

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
queue.touch(msg_id, reservation_id='xxxxxxxx')
```
- msg_id: Message id.
- reservation_id: Reservation id of the message.

### Release a reserved message
To release a message that is currently reserved by reservation id, use release:

```python
queue.release(reservation_id='xxxxxxxx', delay=30) # message will be released after delay seconds, 0 by defaults
```

## Push Queues

### Create queue

```python
ironmq = IronMQ()
options = {
  'message_timeout': 120,
  'message_expiration': 24 * 3600,
  'push': {
    'subscribers': [
      {
        'name': 'subscriber_name',
        'url': 'http://rest-test.iron.io/code/200?store=key1',
        'headers': {
          'Content-Type': 'application/json'
        }
      }
    ],
    'retries': 3,
    'retries_delay': 30,
    'error_queue': 'error_queue_name'
  }
}
ironmq.create_queue('queue_name', options)
```

**Options:**

* `type`: String or symbol. Queue type. `:pull`, `:multicast`, `:unicast`. Field required and static.
* `message_timeout`: Integer. Number of seconds before message back to queue if it will not be deleted or touched.
* `message_expiration`: Integer. Number of seconds between message post to queue and before message will be expired.

**Push queues only:**

* `push: subscribers`: An array of subscriber hashes containing a `name` and a `url` required fields,
and optional `headers` hash. `headers`'s keys are names and values are means of HTTP headers.
This set of subscribers will replace the existing subscribers.
To add or remove subscribers, see the add subscribers endpoint or the remove subscribers endpoint.
See below for example json.
* `push: retries`: How many times to retry on failure. Default is 3. Maximum is 100.
* `push: retries_delay`: Delay between each retry in seconds. Default is 60.
* `push: error_queue`: String. Queue name to post push errors to.

--

### Update Queue Information

Same as create queue

### Add subscribers to a push queue

```python
queue.add_subscribers(["http://endpoint1.com", "https://end.point.com/2"])
```

### Remove subscribers from a push queue

```python
queue.remove_subscribers()
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
q.remove_alerts()
```

### Remove single alert from a queue

```python
q.remove_alert('5305d3b5a3e920763013c796')
```

### Delete a queue

To delete a queue, use `delete_queue`:

```python
queue.delete_queue()
```

# Full Documentation

You can find more documentation here:

* http://iron.io
* http://dev.iron.io
