import iron_core
import urllib
try:
    import json
except:
    import simplejson as json

class Message:
    id = None
    body = None
    timeout = None
    delay = None
    expires_in = None

    __json_attrs = ["body"]
    __duration_attrs = ["delay", "expires_in"]
    __ignore = []
    __aliases = {}

    def __set(self, attr, value):
        setattr(self, attr, value)

    def __init__(self, body=None, values=None, **kwargs):
        if values is None:
            values = {}
        if body is not None:
            values['body'] = body
        attrs = [x for x in vars(self.__class__).keys() if not x.startswith("__")]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                self.__set(self.__aliases[prop], values[prop])

class Queue:
    id = None
    name = None
    size = None
    total_messages = None
    project_id = None
    retries = None
    push_type = None
    retries_delay = None
    subscribers = None
    is_push_queue = False

    __ignore = []
    __aliases = {}
    __push_fields = ["subscribers", "push_type", "retries", "retries_delay"]

    def __set(self, attr, value):
        setattr(self, attr, value)

    def __init__(self, name=None, values={}, **kwargs):
        if values is None:
            values = {}
        if name is not None:
            values['name'] = name
        attrs = [x for x in vars(self.__class__).keys() if not x.startswith("__")]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                self.__set(self.__aliases[prop], values[prop])

class Subscription:
    id = None
    url = None
    status = None
    status_code = None
    retries_remaining = None
    retries_delay = None

    __ignore = []
    __aliases = {}
    
    def __set(self, attr, value):
        setattr(self, attr, value)

    def __init__(self, url=None, values={}, **kwargs):
        if values is None:
            values = {}
        if url is not None:
            values['url'] = url
        attrs = [x for x in vars(self.__class__).keys() if not x.startswith("__")]
        for k in kwargs.keys():
            values[k] = kwargs[k]

        for prop in values.keys():
            if prop in attrs and prop not in self.__ignore:
                self.__set(prop, values[prop])
            elif prop in self.__aliases:
                self.__set(self.__aliases[prop], values[prop])

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
            q = Queue(values=queue)
            if "subscribers" in queue:
                q.subscribers = []
                for subscriber in queue["subscribers"]:
                    q.subscribers.append(Subscription(subscriber))
            queues.append(q)
        return queues

    def queue(self, queue):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        resp = self.client.get("queues/%s" % queue)
        raw_queue = resp["body"]
        for queue in raw_queues:
            q = Queue(values=queue)
            if "subscribers" in queue:
                q.subscribers = []
                for subscriber in queue["subscribers"]:
                    q.subscribers.append(Subscription(subscriber))
            queues.append(q)
        return Queue(values=raw_queue)

    def update(self, queue=None, **kwargs):
        if queue is None:
            queue = Queue(**kwargs)
        if queue.name is None or queue.name == "":
            raise ValueError("queue.name is required.")
        queue_data = {}
        if queue.subscribers is not None:
            queue_data["subscribers"] = [subscriber.__serialize() for subscriber in queue.subscribers]
        if queue.push_type is not None:
            queue_data["push_type"] = queue.push_type
        if queue.retries is not None:
            queue_data["retries"] = queue.retries
        if queue.retries_delay is not None:
            queue_data["retries_delay"] = queue.retries_delay
        data = json.dumps(queue_data)
        headers = {"Content-Type": "application/json"}
        resp = self.client.post("queues/%s" % queue.name, body=data, headers=headers)
        q = Queue(resp["body"])
        if "subscribers" in resp["body"]:
            q.subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q.subscribers.append(Subscription(subscriber))
        return q

    def delete(self, queue, message=None, safe_mode=True):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        if message is not None and  isinstance(message, Message):
            if message.id is None:
                raise ValueError("message object was passed, but it had no ID set.")
            message = message.id
        endpoint = "queues/%s" % queue
        if safe_mode and (message is None or message is not 0):
            raise ValueError("Safe mode is on and message was not explicitly set or does not have an ID of 0. If this call was supposed to delete a queue, set safe_mode=False or message=0.")
        else if message is None or message is 0:
            endpoint = "%s/messages/%s" % (endpoint, message)
        resp = self.client.delete(endpoint)
        return True

    def subscribe(self, queue, subscribers, ignore_empty=False):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
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
        resp = self.client.post("queues/%s/subscribers" % queue, body=data, headers=headers)
        q = Queue(resp["body"])
        if "subscribers" in resp["body"]:
            q.subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q.subscribers.append(Subscription(subscriber))
        return q

    def unsubscribe(self, queue, subscribers):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
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
        resp = self.client.delete("queues/%s/subscribers" % queue, body=data, headers=headers)
        q = Queue(resp["body"])
        if "subscribers" in resp["body"]:
            q.subscribers = []
            for subscriber in resp["body"]["subscribers"]:
                q.subscribers.append(Subscription(subscriber))
        return q

    def clear(self, queue):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        resp = self.client.clear("queues/%s" % queue)
        return True

    def post(self, queue, messages, ignore_empty=False):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
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
        resp = self.client.post("queues/%s/messages" % queue, body=data, headers=headers)
        messages = []
        for i, msg in msgs:
            msg.id = resp["body"]["ids"][i]
            message = Message(values=message)
            messages.append(message)
        return messages

    def get(self, queue, count=None, timeout=None):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        querystring = ""
        if count is not None or timeout is not None:
            querystring += "?"
        if count is not None:
            querystring += "n=%s", count
        if count is not None and timeout is not None:
            querystring += "&"
        if timeout is not None:
            querystring += "timeout=%s", timeout
        resp = self.client.get("queues/%s/messages%s" % (queue, querystring))
        messages = []
        for msg in resp["body"]["messages"]:
            message = Message(values=msg)
            messages.append(message)
        return messages

    def peek(self, queue, count=None):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        querystring = ""
        if count is not None:
            querystring += "?n=%s" % count
        resp = self.client.get("queues/%s/messages/peek%s" % (queue, querystring))
        messages = []
        for msg in resp["body"]["messages"]:
            message = Message(values=msg)
            messages.append(message)
        return messages

    def touch(self, queue, message):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        if isinstance(message, Message):
            if message.id is None:
                raise ValueError("message.id is not set, but is required.")
            message = message.id
        data = json.dumps({})
        headers = {"Content-Type": "application/json"}
        resp = self.client.post("queues/%s/messages/%s/touch" % (queue, message), body=data, headers=headers)
        return True

    def release(self, queue, message, no_delay=False):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        data = {}
        if isinstance(message, Message):
            if message.id is None:
                raise ValueError("message.id is not set, but is required.")
            if not no_delay and message.delay is not None:
                data["delay"]: message.delay
            message = message.id
        data = json.dumps(data)
        headers = {"Content-Type": "application/json"}
        resp = self.client.post("queues/%s/messages/%s/release" % (queue, message), body=data, headers=headers)
        return True

    def push_status(self, queue, message):
        if isinstance(queue, Queue):
            if queue.name is None or queue.name == "":
                raise ValueError("queue.name is required.")
            queue = queue.name
        if isinstance(message, Message):
            if message.id is None:
                raise ValueError("message.id is not set, but is required.")
            message = message.id
        resp = self.client.get("queues/%s/messages/%s/subscribers" % (queue, message))
        subscriptions = []
        for subscriber in resp["body"]["subscribers"]:
            subscriptions.append(Subscription(values=subscriber))
        return subscriptions

    #########################################################################
    ########################### LEGACY METHODS ##############################
    #########################################################################

    def getQueues(self, page=None, project_id=None):
        """Execute an HTTP request to get a list of queues and return it.

        Keyword arguments:
        project_id -- The project ID to get queues from. Defaults to the
                      project ID set when initialising the wrapper.
        page -- The 0-based page to get queues from. Defaults to None, which
                omits the parameter.
        """
        options = {}
        if page is not None:
            options['page'] = page
        
        query = urllib.urlencode(options)
        url = "queues"
        if query != "":
            url = "%s?%s" % (url, query)
        result = self.client.get(url)
        return [queue["name"] for queue in result["body"]]

    def getQueueDetails(self, queue_name, project_id=None):
        """Execute an HTTP request to get details on a specific queue, and
        return it.

        Keyword arguments:
        queue_name -- The name of the queue to get the details of. (Required)
        project_id -- The ID of the project the queue belongs to. Defaults to
                      the project ID set when initialising the wrapper.
        """
        
        url = "queues/%s" % (queue_name,)
        result = self.client.get(url)
        queue = result["body"]
        return queue

    def deleteMessage(self, queue_name, message_id, project_id=None):
        """Execute an HTTP request to delete a code package.

        Keyword arguments:
        queue_name -- The name of the queue the message is in. (Required)
        message_id -- The ID of the message to be deleted. (Required)
        project_id -- The ID of the project that contains the queue that
                      contains the message. Defaults to the project ID set
                      when initialising the wrapper.
        """

        url = "queues/%s/messages/%s" % (queue_name, message_id)
        result = self.client.delete(url)
        return result["body"]

    def postMessage(self, queue_name, messages=[], project_id=None):
        """Executes an HTTP request to create message on the queue.

        Keyword arguments:
        queue_name -- The name of the queue to add the message to. (Required)
        messages -- An array of messages to be added to the queue.
                    Defaults to [].
        project_id -- The ID of the project the queue is under. Defaults to
                      the project ID set when the wrapper was initialised.
        """
        
        url = "queues/%s/messages" % ( queue_name,)
        msgs = [{'body':msg} if isinstance(msg, basestring) else msg
                for msg in messages]
        data = json.dumps({"messages": msgs})

        result = self.client.post(url=url, body=data, headers= {"Content-Type": "application/json"})

        return result['body']

    def getMessage(self, queue_name, max=None, project_id=None):
        """Executes an HTTP request to get a message off of a queue.

        Keyword arguments:
        queue_name -- The name of the queue a message is being fetched from.
                      (Required)
        max -- The maximum number of messages to pull. Defaults to 1.
        project_id -- The ID of the project that contains the queue the message
                      is to be pulled from. Defaults to the project ID set when
                      the wrapper was initialised.
        """
        
        n = ""
        if max is not None:
            n = "&n=%s" % max
        url = "queues/%s/messages?%s" % ( queue_name, n)
        result = self.client.get(url)
        return result['body']

    def clearQueue(self, queue_name, project_id=None):
        """Executes an HTTP request to clear all contents of a queue.

        Keyword arguments:
        queue_name -- The name of the queue a messages are being cleared from.
                      (Required)
        project_id -- The ID of the project that contains the queue that is
                      being cleared. Defaults to the project ID set when the
                      wrapper was initialised.
        """


        url = "queues/%s/clear" % (queue_name,)
        result = self.client.post(url)
        return result['body']
    
