import iron_core
try:
    import json
except:
    import simplejson as json
import requests

class Message:
    id = None
    body = None
    timeout = None
    delay = None
    expires_in = None
    queue = None

    __ignore = []
    __aliases = {}

    _queue = None
    _client = None

    def __set(self, attr, value):
        setattr(self, attr, value)

    def __init__(self, body=None, values=None, queue=None, client=None, **kwargs):
        if values is None:
            values = {}
        if body is not None:
            values['body'] = body
        if queue is not None:
            if isinstance(queue, Queue):
                if queue._client is not None:
                    self._client = queue._client
                self._queue = queue
            elif isinstance(queue, basestring):
                self._queue = Queue(name=queue, client=client)
            else:
                raise ValueError("Unsupported type passed for queue. Please use a Queue object or a string containing the queue's name.")
        else:
            raise ValueError("Cannot initialize a message without a queue.")
        if client is not None:
            self._client = client
        else:
            raise ValueError("Cannot initialize a message without a client.")
        attrs = [x for x in vars(self.__class__).keys() if not x.startswith("_")]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                self.__set(self.__aliases[prop], values[prop])

    def delete(self):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot delete a message until its queue's name is set.")
        if self.id is None:
            raise ValueError("Cannot delete a message if its ID is not set.")
        endpoint = "queues/%s/messages/%s" % (self._queue.name, self.id)
        try:
            resp = self._client.delete(endpoint)
        except requests.HTTPError:
            if resp["status"] == 404:
                return False
            else:
                resp["resp"].raise_for_status()
        return True

    def touch(self):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot touch a message if its queue's name is not set.")
        if self.id is None:
            raise ValueError("Cannot touch a message if its ID is not set.")
        data = json.dumps({})
        headers = {"Content-Type": "application/json"}
        resp = self._client.post("queues/%s/messages/%s/touch" % (self._queue.name, self.id), body=data, headers=headers)
        return True

    def release(self, delay=None):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot release a message if its queue's name is not set.")
        if self.id is None:
            raise ValueError("Cannot release a message if its ID is not set.")
        data = {}
        if delay is not None:
            data["delay"] = self.delay
        data = json.dumps(data)
        headers = {"Content-Type": "application/json"}
        resp = self._client.post("queues/%s/messages/%s/release" % (self._queue.name, self.id), body=data, headers=headers)
        return True

    def push_status(self):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot get the push status of a message if its queue's name is not set.")
        if self.id is None:
            raise ValueError("Cannot get the push status of a message if its ID is not set.")
        resp = self._client.get("queues/%s/messages/%s/subscribers" % (self._queue.name, self.id))
        subscriptions = []
        for subscriber in resp["body"]["subscribers"]:
            subscriptions.append(Subscription(values=subscriber, queue=self._queue, message=self, client=self._client))
        return subscriptions

class Queue:
    name = None
    _id = None
    _size = None
    _total_messages = None
    _project_id = None
    _retries = None
    _push_type = None
    _retries_delay = None
    _subscribers = None
    
    _client = None

    __ignore = ['id']
    __aliases = {'id': '_id', 'size': '_size', 'total_messages': '_total_messages', 'project_id': '_project_id', 'retries': '_retries', 'push_type': '_push_type', 'retries_delay': '_retries_delay', 'subscribers': '_subscribers'}

    def __set(self, attr, value):
        setattr(self, attr, value)

    def __init__(self, name=None, values={}, client=None, **kwargs):
        if values is None:
            values = {}
        if name is not None:
            values['name'] = name
        if client is not None:
            self._client = client
        else:
            raise ValueError("Cannot instantiate a queue without a client.")
        attrs = [x for x in vars(self.__class__).keys() if not x.startswith("__")]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                print "Setting %s to %s" % (self.__aliases[prop], values[prop])
                self.__set(self.__aliases[prop], values[prop])

    def info(self):
        if self.name is None or self.name == "":
            raise ValueError("Cannot get queue information until the queue's name attribute is set.")
        resp = self._client.get("queues/%s" % self.name)
        raw_queue = resp["body"]
        q = Queue(name=self.name, values=raw_queue, client=self._client)
        if "subscribers" in raw_queue:
            q._subscribers = []
            for subscriber in queue["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, queue=q, client=self._client))
        return q

    def is_push_queue(self):
        return self.push_type() is None

    def is_new(self):
        return self.id() is None

    def id(self):
        if self._id is None:
            self._id = self.info()._id
        return self._id

    def size(self):
        return self.info()._size

    def total_messages(self):
        return self.info()._total_messages

    def retries(self):
        return self.info()._retries

    def push_type(self):
        return self.info()._push_type

    def retries_delay(self):
        return self.info()._retries_delay

    def subscribers(self):
        return self.info()._subscribers

    def subscribe(self, subscribers, ignore_empty=False):
        if self.name is None or self.name == "":
            raise ValueError("Cannot subscribe to a queue until its name attribute is set.")
        subscriptions = []
        if type(subscribers) is not list:
            subscribers = [subscribers]
        for subscriber in subscribers:
            if isinstance(subscriber, Subscription):
                if subscriber.url is None or subscriber.url == "":
                    if ignore_empty:
                        continue
                    else:
                        raise ValueError("subscriber.url is required, but was not set.")
                subscriptions.append(subscriber.url)
            else:
                subscriptions.append(subscriber)
        data = json.dumps({"subscribers": subcriptions})
        headers = {"Content-Type": "application/json"}
        resp = self._client.post("queues/%s/subscribers" % self.name, body=data, headers=headers)
        q = Queue(values=resp["body"], client=self._client)
        if "subscribers" in resp["body"]:
            q._subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, client=self._client, queue=q))
        return q

    def unsubscribe(self, subscribers, ignore_empty=False):
        if self.name is None or self.name == "":
            raise ValueError("Cannot unsubscribe from a queue until its name attribute is set.")
        subscriptions = []
        if type(subscribers) is not list:
            subscribers = [subscribers]
        for subscriber in subscribers:
            if isinstance(subscriber, Subscription):
                if subscriber.url is None or subscriber.url == "":
                    if ignore_empty:
                        continue
                    else:
                        raise ValueError("subscriber.url is required, but was not set.")
                subscriptions.append(subscriber.url)
            else:
                subscriptions.append(subscriber)
        data = json.dumps({"subscribers": subcriptions})
        headers = {"Content-Type": "application/json"}
        resp = self._client.delete("queues/%s/subscribers" % self.name, body=data, headers=headers)
        q = Queue(resp["body"])
        if "subscribers" in resp["body"]:
            q._subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, client=self._client, queue=q))
        return q

    def clear(self):
        if self.name is None or self.name == "":
            raise ValueError("Cannot clear a queue until its name attribute is set.")
        resp = self._client.post("queues/%s/clear" % self.name)
        return True

    def post(self, messages, ignore_empty=False):
        if self.name is None or self.name == "":
            raise ValueError("Cannot post to a queue until its name attribute is set.")
        if type(messages) is not list:
            messages = [messages]
        msgs = []
        for message in messages:
            if isinstance(message, Message):
                if message.body is None:
                    if ignore_empty:
                        continue
                    else:
                        raise ValueError("message.body is required but was not set.")
                msg = {"body": message.body}
                if message.timeout is not None:
                    msg["timeout"] = message.timeout
                if message.delay is not None:
                    msg["delay"] = message.delay
                if message.expires_in is not None:
                    msg["expires_in"] = message.expires_in
            elif isinstance(message, basestring):
                msg = {"body": message}
            else:
                msg = message
            msgs.append(msg)
        data = json.dumps({"messages": msgs})
        headers = {"Content-Type": "application/json"}
        resp = self._client.post("queues/%s/messages" % self.name, body=data, headers=headers)
        return True

    def get(self, count=None, timeout=None):
        if self.name is None or self.name == "":
            raise ValueError("Cannot get messages from a queue until its name attribute is set.")
        querystring = ""
        if count is not None or timeout is not None:
            querystring += "?"
        if count is not None:
            querystring += "n=%s", count
        if count is not None and timeout is not None:
            querystring += "&"
        if timeout is not None:
            querystring += "timeout=%s", timeout
        resp = self._client.get("queues/%s/messages%s" % (self.name, querystring))
        messages = []
        for msg in resp["body"]["messages"]:
            message = Message(values=msg, client=self._client, queue=self)
            messages.append(message)
        if len(messages) == 1:
            messages = messages[0]
        return messages

    def peek(self, count=None):
        if self.name is None or self.name == "":
            raise ValueError("Cannot peek at a queue's messages until its name attribute is set.")
        querystring = ""
        if count is not None:
            querystring += "?n=%s" % count
        resp = self._client.get("queues/%s/messages/peek%s" % (self.name, querystring))
        messages = []
        for msg in resp["body"]["messages"]:
            message = Message(values=msg, queue=self, client=self._client)
            messages.append(message)
        if len(messages) == 1:
            messages = messages[0]
        return messages

    def update(self, push_type=None, subscribers=None, retries=None, retries_delay=None):
        queue_data = {}
        if subscribers is not None:
            queue_data["subscribers"] = [subscriber._serialize() for subscriber in subscribers]
        if push_type is not None:
            queue_data["push_type"] = push_type
        if retries is not None:
            queue_data["retries"] = retries
        if retries_delay is not None:
            queue_data["retries_delay"] = retries_delay
        data = json.dumps(queue_data)
        headers = {"Content-Type": "application/json"}
        resp = self._client.post("queues/%s" % self.name, body=data, headers=headers)
        q = Queue(values=resp["body"], client=self._client)
        if "subscribers" in resp["body"]:
            q._subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, queue=q, client=self._client))
        return q

    def delete(self):
        if self.name is None or self.name == "":
            raise ValueError("Cannot delete a queue until its name attribute is set.")
        endpoint = "queues/%s" % self.name
        try:
            resp = self._client.delete(endpoint)
        except requests.HTTPError:
            if resp["status"] == 404:
                return False
            else:
                resp["resp"].raise_for_status()
        return True

class Subscription:
    url = None
    _id = None
    _status = None
    _status_code = None
    _retries_remaining = None
    _retries_delay = None
    
    _message = None
    _queue = None
    _client = None

    __ignore = []
    __aliases = {'status': '_status', 'status_code': '_status_code', 'retries_remaining': '_retries_remaining', 'retries_delay': '_retries_delay'}
    
    def __set(self, attr, value):
        setattr(self, attr, value)

    def __init__(self, url=None, values={}, message=None, queue=None, client=None, **kwargs):
        if values is None:
            values = {}
        if url is not None:
            values['url'] = url
        if message is not None:
            if isinstance(message, Message):
                if message._queue is not None:
                    self._queue = message._queue
                    if self._queue._client is not None:
                        self._client = queue._client
                if message._client is not None:
                    self._client = message._client
                self._message = message
            elif isinstance(message, basestring):
                self._message = Message(id=message, queue=queue, client=client)
            else:
                raise ValueError("Unsupported type passed as a message. Please pass a Message object or a string containing the message's body.")
        if queue is not None:
            if isinstance(queue, Queue):
                if queue._client is not None:
                    self._client = queue._client
                self._queue = queue
            elif isinstance(queue, basestring):
                self._queue = Queue(name=queue, client=client)
            else:
                raise ValueError("Unsupported type passed as a queue. Please pass a Queue object or a string containing the queue's name.")
        if client is not None:
            self._client = client
        if self._queue is None:
            raise ValueError("Cannot initialize a subscription without a queue.")
        if self._client is None:
            raise ValueError("Cannot initialize a subscription without a client.")
        attrs = [x for x in vars(self.__class__).keys() if not x.startswith("__")]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                self.__set(self.__aliases[prop], values[prop])

    def acknowledge(self):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot acknowledge a message from a subscription whose queue's name is not set.")
        if self._message is None or self._message.id is None:
            raise ValueError("Cannot acknowledge a message if its ID is not set.")
        if self._id is None:
            raise ValueError("Cannot acknowledge a message if the subscription's ID is not set.")
        endpoint = "queues/%s/messages/%s/subscribers/%s" % (self._queue.name, self._message.id, self._id)
        try:
            resp = self._client.delete(endpoint)
        except requests.HTTPError:
            if resp["status"] == 404:
                return False
            else:
                resp["resp"].raise_for_status()
        return True

class IronMQ:
    NAME = "iron_mq_python"
    VERSION = "1.0.0"
    client = None

    def __init__(self, **kwargs):
        """Prepare a configured instance of the API wrapper and return it.

        Keyword arguments are passed directly to iron_core_python; consult its
        documentation for a full list and possible values."""
        self.client = iron_core.IronClient(name=IronMQ.NAME,
                version=IronMQ.VERSION, product="iron_mq", **kwargs)

    def queues(self, per_page=None, page=None):
        queues = []
        querystring = ""
        if per_page is not None or page is not None:
            querystring += "?"
        if per_page is not None:
            querystring += "per_page=%s" % per_page
        if per_page is not None and page is not None:
            querystring += "&"
        if page is not None:
            querystring += "page=%s" % page
        resp = self.client.get("queues%s" % querystring)
        raw_queues = resp["body"]
        for queue in raw_queues:
            q = Queue(values=queue, client=self.client)
            if "subscribers" in queue:
                q._subscribers = []
                for subscriber in queue["subscribers"]:
                    q._subscribers.append(Subscription(values=subscriber, queue=q, client=self.client))
            queues.append(q)
        return queues

    def get(self, queue):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        resp = self.client.get("queues/%s" % queue)
        raw_queue = resp["body"]
        q = Queue(name=queue, values=raw_queue, client=self.client)
        if "subscribers" in raw_queue:
            q._subscribers = []
            for subscriber in queue["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, queue=q, client=self.client))
        return q
