import iron_core
try:
    import json
except:
    import simplejson as json
import requests
import urllib

class IronMQRouter(object):
    def to_path(self, base_path, **kwargs):
        """Build a URL with query parameters"""
        query = urllib.urlencode(self.remove_empty(kwargs))
        fullpath = urllib.quote(base_path) + ('?' + query if query != '' else '')
        return fullpath

    def remove_empty(self, args):
        """Removes None valued keys from dict"""
        for (key, value) in args.items():
            if value is None or value == "": del args[key]

        return args


class Message(IronMQRouter):
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

        # Use Queue's client by default if possible
        if self._client is None and client is not None:
            if not isinstance(client, IronMQ): raise ValueError('`client` argument must be IronMQ instance')
            self._client = client
        if self._client is None: raise ValueError("Cannot initialize a message without a client.")

        attrs = [x for x in vars(self.__class__).keys() if not (x.startswith("_") or hasattr(vars(self.__class__)[x], '__call__'))]
        if values is None: values = {}
        if body is not None: values['body'] = body
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
        endpoint = super(Message, self).to_path("queues/%s/messages/%s" % (self._queue.name, self.id))
        try:
            resp = self._client.delete(endpoint)
        except requests.HTTPError as e:
            if e.response.status_code == request.codes.not_found:
                return False
            else:
                e.response.raise_for_status()
        return True

    def touch(self):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot touch a message if its queue's name is not set.")
        if self.id is None:
            raise ValueError("Cannot touch a message if its ID is not set.")
        data = json.dumps({})
        headers = {"Content-Type": "application/json"}
        path = super(Message, self).to_path("queues/%s/messages/%s/touch" % (self._queue.name, self.id))
        resp = self._client.post(path, body=data, headers=headers)
        return True

    def release(self, delay=None):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot release a message if its queue's name is not set.")
        if self.id is None:
            raise ValueError("Cannot release a message if its ID is not set.")
        data = {}
        if delay is not None:
            data["delay"] = delay
        data = json.dumps(data)
        headers = {"Content-Type": "application/json"}
        path = super(Message, self).to_path("queues/%s/messages/%s/release" % (self._queue.name, self.id))
        resp = self._client.post(path, body=data, headers=headers)
        return True

    def push_status(self):
        if self._queue is None or self._queue.name is None or self._queue.name == "":
            raise ValueError("Cannot get the push status of a message if its queue's name is not set.")
        if self.id is None:
            raise ValueError("Cannot get the push status of a message if its ID is not set.")

        path = super(Message, self).to_path("queues/%s/messages/%s/subscribers" % (self._queue.name, self.id))
        resp = self._client.get(path)
        subscriptions = []
        for subscriber in resp["body"]["subscribers"]:
            subscriptions.append(Subscription(values=subscriber, queue=self._queue, message=self, client=self._client))
        return subscriptions

    def raw(self):
        return {'id': self.id,
                'body': self.body,
                'timeout': self.timeout,
                'delay': self.delay,
                'expires_in': self.expires_in}


class Queue(IronMQRouter):
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
        attrs = [x for x in vars(self.__class__).keys() if not (x.startswith("_") or hasattr(vars(self.__class__)[x], '__call__'))]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                self.__set(self.__aliases[prop], values[prop])

    # `raw` is backward compatibility flag, True by default
    def info(self, raw=True):
        if self.name is None or self.name == "":
            raise ValueError("Cannot get queue information until the queue's name attribute is set.")

        resp = self._client.get(super(Queue, self).to_path("queues/%s" % self.name))
        if raw:
            return resp['body']
        else:
            q = Queue(name=self.name, values=resp['body'], client=self._client)
            if 'subscribers' in resp['body']:
                q._subscribers = []
                for subscriber in raw_queue['subscribers']:
                    q._subscribers.append(Subscription(values=subscriber, queue=q, client=self._client))
            return q

    def is_push_queue(self):
        return self.push_type() is not None

    def is_new(self):
        i = None
        try:
            self.id()
        except requests.HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                return True
            else:
                e.response.raise_for_status()
        return self.id() is None

    def id(self):
        if self._id is None:
            self._id = self.info(raw=False)._id
        return self._id

    def size(self):
        return self.info(raw=False)._size

    def total_messages(self):
        return self.info(raw=False)._total_messages

    def retries(self):
        return self.info(raw=False)._retries

    def push_type(self):
        return self.info(raw=False)._push_type

    def retries_delay(self):
        return self.info(raw=False)._retries_delay

    def subscribers(self):
        return self.info(raw=False)._subscribers

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
                subscriptions.append({"url": subscriber.url})
            else:
                subscriptions.append({"url": subscriber})
        data = json.dumps({"subscribers": subscriptions})
        headers = {"Content-Type": "application/json"}
        resp = self._client.post(super(Queue, self).to_path("queues/%s/subscribers" % self.name),
                                 body=data, headers=headers)
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
                subscriptions.append({"url": subscriber.url})
            else:
                subscriptions.append({"url": subscriber})
        data = json.dumps({"subscribers": subscriptions})
        headers = {"Content-Type": "application/json"}
        resp = self._client.delete(super(Queue, self).to_path("queues/%s/subscribers" % self.name),
                                   body=data, headers=headers)
        q = Queue(values=resp["body"], client=self._client)
        if "subscribers" in resp["body"]:
            q._subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, client=self._client, queue=q))
        return q

    def clear(self):
        if self.name is None or self.name == "":
            raise ValueError("Cannot clear a queue until its name attribute is set.")
        resp = self._client.post(super(Queue, self).to_path("queues/%s/clear" % self.name))
        return True

    def post(self, *messages, **kwargs):
        if self.name is None or self.name == "":
            raise ValueError("Cannot post to a queue until its name attribute is set.")

        if 'ignore_empty' in kwargs.keys():
            ignore_empty = kwargs['ignore_empty']
            del kwargs['ignore_empty']
        else: ignore_empty = False

        attrs = super(Queue, self).remove_empty(kwargs)

        msgs = []
        for message in messages:
            if isinstance(message, Message):
                if message.body is None:
                    if ignore_empty: continue
                    else: raise ValueError("message.body is required but was not set.")
                msg = message.raw()
            else:
                msg = {'body': message}
                msg.update(attrs)
            msgs.append(msg)
        data = json.dumps({"messages": msgs})
        headers = {"Content-Type": "application/json"}
        resp = self._client.post(super(Queue, self).to_path("queues/%s/messages" % self.name),
                                 body=data, headers=headers)
        return True

    def get(self, count=None, timeout=None):
        if self.name is None or self.name == "":
            raise ValueError("Cannot get messages from a queue until its name attribute is set.")

        path = super(Queue, self).to_path("queues/%s/messages" % self.name, n=count, timeout=timeout)
        resp = self._client.get(path)

        messages = []
        for msg in resp["body"]["messages"]:
            message = Message(values=msg, client=self._client, queue=self)
            messages.append(message)
        if count is None or count < 2:
            if len(messages) > 0:
                messages = messages[0]
            else:
                messages = None
        return messages

    def peek(self, count=None):
        if self.name is None or self.name == "":
            raise ValueError("Cannot peek at a queue's messages until its name attribute is set.")

        path = super(Queue, self).to_path("queues/%s/messages/peek" % self.name, n=count)
        resp = self._client.get(path)

        messages = []
        if resp["body"]["messages"] is not None:
            for msg in resp["body"]["messages"]:
                message = Message(values=msg, queue=self, client=self._client)
                messages.append(message)
        if count is None or count < 2:
            messages = (messages[0] if len(messages) > 0 else None)

        return messages

    def update(self, push_type=None, subscribers=None, retries=None, retries_delay=None, ignore_empty=True):
        queue_data = super(Queue, self).remove_empty({'push_type': push_type,
                                                      'retries': retries,
                                                      'retries_delay': retries_delay})
        if subscribers is not None:
            subscriptions = []
            if type(subscribers) is not list:
                subscribers = [subscribers]
            for subscriber in subscribers:
                if isinstance(subscriber, Subscription):
                    if (subscriber.url is None or subscriber.url == "") and ignore_empty:
                        continue
                    elif (subscriber.url is None or subscriber.url == "") and not ignore_empty:
                        raise ValueError("ignore_empty is false and an empty subscriber was encountered.")
                    subscriptions.append({"url": subscriber.url})
                elif isinstance(subscriber, basestring):
                    if subscriber == "":
                        if ignore_empty:
                            continue
                        else:
                            raise ValueError("ignore_empty is false and an empty subscriber was encountered.")
                    subscriptions.append({"url":subscriber})
                else:
                    raise ValueError("Unacceptable type passed as a subscriber. Only URLs as strings or Subscriber objects are acceptable.")
            queue_data["subscribers"] = subscriptions
        if not push_type in ['multicast', 'unicast']:
            raise ValueError("push_type must be multicast or unicast")

        data = json.dumps(queue_data)
        headers = {"Content-Type": "application/json"}
        resp = self._client.post(super(Queue, self).to_path("queues/%s" % self.name),
                                 body=data, headers=headers)
        q = Queue(values=resp["body"], client=self._client)
        if "subscribers" in resp["body"]:
            q._subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q._subscribers.append(Subscription(values=subscriber, queue=q, client=self._client))
        return q

    def delete(self, *args):
        if self.name is None or self.name == "":
            raise ValueError("Cannot delete until its name attribute is set.")

        # Backward compatibility, bad idea, drop it ASAP
        msg_id = None
        endpoint = None
        if len(args) == 1:
            endpoint = super(Queue, self).to_path("queues/%s/messages/%s" % (self.name % args[0]))
        else:
            endpoint = super(Queue, self).to_path("queues/%s" % self.name)

        try:
            resp = self._client.delete(endpoint)
            self._id = None
        except requests.HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                return False
            else:
                e.response.raise_for_status()
        return True


class Subscription(IronMQRouter):
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
        attrs = [x for x in vars(self.__class__).keys() if not (x.startswith("_") or hasattr(vars(self.__class__)[x], '__call__'))]
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
        endpoint = super(Subscription, self).to_path("queues/%s/messages/%s/subscribers/%s" % (self._queue.name, self._message.id, self._id))
        try:
            resp = self._client.delete(endpoint)
        except requests.HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                return False
            else:
                e.response.raise_for_status()
        return True

class IronMQ(IronMQRouter):
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
        resp = self.client.get(super(IronMQ, self).to_path("queues", page=page, per_page=per_page))
        raw_queues = resp["body"]

        queues = []
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
        q = None
        try:
            path = super(IronMQ, self).to_path("queues/%s" % queue)
            resp = self.client.get(path)
            raw_queue = resp["body"]
            q = Queue(name=queue, values=raw_queue, client=self.client)
            if "subscribers" in raw_queue:
                q._subscribers = []
                for subscriber in raw_queue["subscribers"]:
                    q._subscribers.append(Subscription(values=subscriber, queue=q, client=self.client))
        except requests.HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                q = Queue(queue, client=self.client)
            else:
                e.response.raise_for_status()
        return q

    # More aliases for readability
    def queue(self, queue):
        return self.get(queue)

    def get_queue(self, queue):
        return self.get(queue)
