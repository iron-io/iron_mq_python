import iron_core
import urllib
try:
    import json
except:
    import simplejson as json

class Queue:
    client = None
    name = None

    def __init__(self, mq, name):
        """Creates object for manipulating a queue.

        Arguments:
        mq -- An instance of IronMQ.
        name -- The name of the queue.
        """

        self.client = mq.client
        self.name = name


    def info(self):
        """Execute an HTTP request to get details on a queue, and
        return it.
        """
        
        url = "queues/%s" % (self.name,)
        result = self.client.get(url)
        return result["body"]


    def size(self):
        """Queue size"""
        return self.info()['size']


    def id(self):
        """Queue ID"""
        return self.info()['id']


    def total_messages(self):
        """Queue total messages count"""
        return self.info()['total_messages']


    def clear(self):
        """Executes an HTTP request to clear all contents of a queue.
        """

        url = "queues/%s/clear" % (self.name,)
        result = self.client.post(url)
        return result['body']


    def delete(self,  message_id):
        """Execute an HTTP request to delete a message from queue.

        Arguments:
        message_id -- The ID of the message to be deleted.
        """

        url = "queues/%s/messages/%s" % (self.name, message_id)
        result = self.client.delete(url)
        return result["body"]


    def post(self, *messages):
        """Executes an HTTP request to create message on the queue.
        Creates queue if not existed.

        Arguments:
        messages -- An array of messages to be added to the queue.
        """
        
        url = "queues/%s/messages" % (self.name,)

        msgs = [{'body':msg} if isinstance(msg, basestring) else msg
                for msg in messages]
        data = json.dumps({"messages": msgs})

        result = self.client.post(url=url, body=data,
                                  headers={"Content-Type":"application/json"})

        return result['body']


    def get(self, max=None):
        """Executes an HTTP request to get a message off of a queue.

        Keyword arguments:
        max -- The maximum number of messages to pull. Defaults to 1.
        """
        
        n = ""
        if max is not None:
            n = "&n=%s" % max
        url = "queues/%s/messages?%s" % (self.name, n)
        result = self.client.get(url)
        return result['body']


class IronMQ:
    NAME = "iron_mq_python"
    VERSION = "0.3"
    client = None
    name = None

    def __init__(self, name=None, **kwargs):
        """Prepare a configured instance of the API wrapper and return it.

        Keyword arguments are passed directly to iron_core_python; consult its
        documentation for a full list and possible values."""
        if name is not None:
            self.name = name
        self.client = iron_core.IronClient(name=IronMQ.NAME,
                version=IronMQ.VERSION, product="iron_mq", **kwargs)


    def queues(self, page=None):
        """Execute an HTTP request to get a list of queues and return it.

        Keyword arguments:
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


    def queue(self, queue_name):
        """Returns Queue object.

        Arguments:
        queue_name -- The name of the queue.
        """

        return Queue(self, queue_name)


    # DEPRECATED

    def getQueues(self, page=None, project_id=None):
        return self.queues(page=page)

    def getQueueDetails(self, queue_name, project_id=None):
        return self.queue(queue_name).info()

    def deleteMessage(self, queue_name, message_id, project_id=None):
        return self.queue(queue_name).delete(message_id)

    def postMessage(self, queue_name, messages=[], project_id=None):
        return self.queue(queue_name).post(*messages)

    def getMessage(self, queue_name, max=None, project_id=None):
        return self.queue(queue_name).get(max=max)

    def clearQueue(self, queue_name, project_id=None):
        return self.queue(queue_name).clear()
