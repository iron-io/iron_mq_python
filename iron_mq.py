import iron_core
import urllib
try:
    import json
except:
    import simplejson as json

class Queue(object):
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

    def delete_multiple(self,  *messages):
        """Execute an HTTP request to delete messages from queue.

        Arguments:
        messages -- An array of messages to be deleted from the queue.
        """
        url = "queues/%s/messages" % self.name
        
        data = json.dumps({"ids": messages})
        result = self.client.delete(url=url, body=data,
                                  headers={"Content-Type":"application/json"})
        return result["body"]

    def post(self, *messages):
        """Executes an HTTP request to create message on the queue.
        Creates queue if not existed.

        Arguments:
        messages -- An array of messages to be added to the queue.
        """
        url = "queues/%s/messages" % self.name

        msgs = [{'body':msg} if isinstance(msg, basestring) else msg
                for msg in messages]
        data = json.dumps({"messages": msgs})

        result = self.client.post(url=url, body=data,
                                  headers={"Content-Type":"application/json"})

        return result['body']

    def get(self, max=None, timeout=None, wait=None):
        """Executes an HTTP request to get a message off of a queue.

        Keyword arguments:
        max -- The maximum number of messages to pull. Defaults to 1.
        """
        url = "queues/%s/messages" % self.name
        qitems = {}
        if max is not None:
            qitems["n"] = max
        if timeout is not None:
            qitems["timeout"] = timeout
        if wait is not None:
            qitems["wait"] = wait
        qs = []
        for k, v in qitems.items():
            qs.append("%s=%s" % (k, v))
        qs = "&".join(qs)
        if qs != "":
            url = "%s?%s" % (url, qs)

        result = self.client.get(url)

        return result['body']

    def get_message_by_id(self, message_id):
        url = "queues/%s/messages/%s" % (self.name, message_id)
        response = self.client.get(url)
        return response['body']

    def peek(self, max=None):
        url = "queues/%s/messages/peek" % self.name
        if max is not None:
            url = "%s?n=%s" % (url, max)

        response = self.client.get(url)

        return response['body']

    def touch(self, message_id):
        url = "queues/%s/messages/%s/touch" % (self.name, message_id)

        response = self.client.post(url, body=json.dumps({}),
                                    headers={"Content-Type":"application/json"})

        return response['body']

    def release(self, message_id, delay=0):
        url = "queues/%s/messages/%s/release" % (self.name, message_id)
        body = {}
        if delay > 0:
            body['delay'] = delay
        body = json.dumps(body)

        response = self.client.post(url, body=body,
                                    headers={"Content-Type":"application/json"})

        return response['body']

    def update(self, subscribers=None, **kwargs):
        url = "queues/%s" % self.name
        body = kwargs
        if subscribers is not None:
            if isinstance(subscribers, list):
                body.update(self._prepare_subscribers(*subscribers))
            else:
                body['subscribers'] = [{'url': subscribers}]
        body = json.dumps(body)

        response = self.client.post(url, body=body,
                                    headers={"Content-Type":"application/json"})

        return response['body']

    def delete_queue(self):
        url = "queues/%s" % self.name

        response = self.client.delete(url)

        return response['body']

    def add_alerts(self, *alerts):
        url = "queues/%s/alerts" % self.name
        body = json.dumps({'alerts': alerts})
        response = self.client.post(url, body=body, headers={"Content-Type":"application/json"})
        return response['body']

    def update_alerts(self, *alerts):
        url = "queues/%s/alerts" % self.name
        body = json.dumps({'alerts': alerts})
        response = self.client.put(url, body=body, headers={"Content-Type":"application/json"})
        return response['body']

    def remove_alerts(self, *alert_ids):
        url = "queues/%s/alerts" % self.name
        body = json.dumps(self._prepare_alert_ids(*alert_ids))
        response = self.client.delete(url, body=body, headers={"Content-Type":"application/json"})
        return response['body']

    def remove_alert(self, alert_id):
        url = "queues/%s/alerts/%s" % (self.name, alert_id)
        response = self.client.delete(url, body={}, headers={"Content-Type":"application/json"})
        return response['body']

    def add_subscribers(self, *subscribers):
        url = "queues/%s/subscribers" % self.name
        body = json.dumps(self._prepare_subscribers(*subscribers))

        response = self.client.post(url, body=body,
                                    headers={"Content-Type":"application/json"})

        return response['body']

    def remove_subscribers(self, *subscribers):
        url = "queues/%s/subscribers" % self.name
        body = json.dumps(self._prepare_subscribers(*subscribers))

        response = self.client.delete(url, body=body,
                                      headers={"Content-Type":"application/json"})

        return response['body']

    def get_message_push_statuses(self, message_id):
        url = "queues/%s/messages/%s/subscribers" % (self.name, message_id)

        response = self.client.get(url)

        return response['body']

    def delete_message_push_status(self, message_id, subscriber_id):
        url = "queues/%s/messages/%s/subscribers/%s" % (self.name, message_id, subscriber_id)

        response = self.client.delete(url)

        return response['body']

    def _prepare_alert_ids(self, *alert_ids):
        alerts = [{'id': id} for id in alert_ids]
        return {'alerts': alerts}

    def _prepare_subscribers(self, *subscribers):
        subscrs = [{'url': ss} for ss in subscribers]

        return {'subscribers': subscrs}

class IronMQ(object):
    NAME = "iron_mq_python"
    VERSION = "0.5"
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


    def queues(self, page=None, per_page=None):
        """Execute an HTTP request to get a list of queues and return it.

        Keyword arguments:
        page -- The 0-based page to get queues from. Defaults to None, which
                omits the parameter.
        """
        options = {}
        if page is not None:
            options['page'] = page
        if per_page is not None:
            options['per_page'] = per_page
        
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
