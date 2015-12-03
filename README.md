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
ironmq = IronMQ(host='mq-aws-us-east-1-1.iron.io',
                project_id='500f7b....b0f302e9',
                token='Et1En7.....0LuW39Q',
                protocol='https', port=443,
                api_version=3,
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

### Push a message(s) on the queue:

```python
queue.post('Hello world')
```

Message can be described by dict:

```python
message = {
    "body" : "Test Message",
    "delay" : 5, # The item will not be available on the queue until this many seconds have passed. Defaults to 0.
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
queue.reserve(max=10, timeout=None, wait=0, delete=False)
```

All fields are optional.

- max: The maximum number of messages to get. Default is 1. Maximum is 100. Note: You may not receive all max messages on every request, the more sparse the queue, the less likely you are to receive all max messages.
- timeout:  After timeout (in seconds), item will be placed back onto queue. You must delete the message from the queue to ensure it does not go back onto the queue. If not set, value from queue is used. Default is 60 seconds, minimum is 30 seconds, and maximum is 86,400 seconds (24 hours).
- wait: Time to long poll for messages, in seconds. Max is 30 seconds. Default 0.
- delete: If true, do not put each message back on to the queue after reserving. Default false.

When you reserve a message from the queue, it will NOT be deleted.
It will eventually go back onto the queue after a timeout if you don't delete it (default timeout is 60 seconds).

### Get message by id

```python
queue.get_message_by_id('xxxxxxxx')
```

### Delete a message from the queue:

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

### Clear a queue:

```python
queue.clear()
```

### Get queue information

```python
queue.info()
 # {u'name': u'queue12',
 # u'project_id': u'54f95a43ecbd7e000800002a',
 # u'message_timeout': 60,
 # u'message_expiration': 604800,
 # u'size': 15,
 # u'total_messages': 17}
queue.size() # 15
queue.name
queue.total_messages() # 17
```

### Peek messages

Get messages without reservation. It does not remove messages from a queue.
So that, after peeking messages, they will be available to reserve or peek.

```python
msgs = queue.peek(max=10) # {"messages": [{'id': '..', 'body': '..'}, ..]}
```

### Touch a message

To extend the reservation on a reserved message, use touch. The message
reservation will be extended by provided `timeout` seconds. If `timeout` is not
set, current queue timeout will be used.

```python
queue.touch(message_id, reservation_id, timeout=10)
```

### Release reserved message

It releases the message by its ID and reservation ID. Optional parameter `delay`
signalise after how many seconds the message must be released.

```python
queue.release(message_id, reservation_id, delay=30)
```

## Queues

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

* `type`: String or symbol. Queue type. `:pull`, `:multicast`, `:unicast`. Field is static. Once set, it cannot be changed.
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

## Push Queues

### Add or update subscribers on a push queue

```python
subscribers = [
    {
        'name': 'first',
        'url': 'http://first.endpoint.xx/process',
        'headers': {
            'Content-Type': 'application/json'
        }
    },
    {
        'name': 'second',
        'url': 'http://second.endpoint.xx/process',
        'headers': {
            'Content-Type': 'application/json'
        }
    }
]
queue.add_subscribers(*subscribers)
```

### Replace subscribers on a push queue

Sets list of subscribers to a queue. Older subscribers will be removed.

```python
subscribers = [
    {
        "name": "the_only",
        "url": "http://my.over9k.host.com/push"
    }
];
queue.replace_subscribers(*subscribers);
```

### Remove subscribers by a name from a push queue

```python
queue.remove_subscribers('first', 'second')
```

### Get the push statuses of a message

```python
queue.get_message_push_statuses(message_id)
```

### Delete a pushed message

If you respond with a 202 status code, the pushed message will be reserved,
not deleted, and should be manually deleted. You can get the message ID,
reservation ID, and subscriber name from push request headers.

```python
queue.delete(message_id, reservation_id, subscriber_name)
```

## Pull queues

### Add alerts to a queue

```python
fixed_desc_alert = {'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'q'}
progressive_asc_alert = {'type': 'progressive', 'direction': 'asc', 'trigger': 10000, 'queue': 'q'}
queue.add_alerts(*[fixed_desc_alert, progressive_asc_alert])
```

#### You can add single alert to a queue

```python
fixed_desc_alert = {'name': 'progressive-alert', 'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'q'}
queue.add_alerts(fixed_desc_alert)
```

### Update alerts in a queue

```python
progressive_asc_alert = {'type': 'progressive', 'direction': 'asc', 'trigger': 5000, 'queue': 'q'}
queue.update_alerts(*[progressive_asc_alert])
```

### Remove alerts from a queue

```python
q.remove_alerts(*[{name: 'progressive-alert'}])
```

### Delete a queue

To delete a queue, use `delete_queue`:

```python
queue.delete_queue()
```

# Full Documentation

You can find more documentation here:

* http://dev.iron.io
* http://iron.io
