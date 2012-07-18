import iron_core
import urllib
try:
    import json
except:
    import simplejson as json

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
    
