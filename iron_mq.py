import iron_core
import urllib

try:
    import json
except:
    import simplejson as json

try:
    basestring
except NameError:
    basestring = str


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

        return result['body']['queue']

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
        """Executes an HTTP request to clear all contents of a queue."""
        url = "queues/%s/messages" % self.name
        result = self.client.delete(url = url,
                                    body = json.dumps({}),
                                    headers={'Content-Type': 'application/json'})

        return result['body']

    def delete(self,  message_id, reservation_id=None, subscriber_name=None):
        """Execute an HTTP request to delete a message from queue.

        Arguments:
        message_id -- The ID of the message to be deleted.
        reservation_id -- Reservation Id of the message. Reserved message could not be deleted without reservation Id.
        subscriber_name -- This is required to acknowledge push after long-processing of message is finished.
        """
        url = "queues/%s/messages/%s" % (self.name, message_id)
        qitems = {}
        if reservation_id is not None:
            qitems['reservation_id'] = reservation_id
        if subscriber_name is not None:
            qitems['subscriber_name'] = subscriber_name
        body = json.dumps(qitems)

        result = self.client.delete(url=url, body=body,
                                    headers={'Content-Type': 'application/json'})

        return result['body']

    def delete_multiple(self, ids=None, messages=None):
        """Execute an HTTP request to delete messages from queue.

        Arguments:
        ids -- A list of messages id to be deleted from the queue.
        messages -- Response to message reserving.
        """
        url = "queues/%s/messages" % self.name

        items = None
        if ids is None and messages is None:
             raise Exception('Please, specify at least one parameter.')
        if ids is not None:
           items = map(lambda item: {'id': item}, ids)
        if messages is not None:
           items = map(lambda item: {'id': item['id'] ,'reservation_id': item['reservation_id']},
                       messages['messages'])

        data = json.dumps({'ids': items})

        result = self.client.delete(url=url, body=data,
                                    headers={'Content-Type': 'application/json'})
        return result['body']

    def post(self, *messages):
        """Executes an HTTP request to create message on the queue.
        Creates queue if not existed.

        Arguments:
        messages -- An array of messages to be added to the queue.
        """
        url = "queues/%s/messages" % self.name

        msgs = [{'body': msg} if isinstance(msg, basestring) else msg
                for msg in messages]
        data = json.dumps({'messages': msgs})

        result = self.client.post(url=url, body=data,
                                  headers={'Content-Type': 'application/json'})

        return result['body']

    def get(self, max=None, timeout=None, wait=None):
        """Deprecated. Use Queue.reserve() instead. Executes an HTTP request to get a message off of a queue.

        Keyword arguments:
        max -- The maximum number of messages to pull. Defaults to 1.
        """
        response = self.reserve(max, timeout, wait)
        return response


    def reserve(self, max=None, timeout=None, wait=None, delete=None):
        """Retrieves Messages from the queue and reserves it.

        Arguments:
        max -- The maximum number of messages to reserve. Defaults to 1.
        timeout -- Timeout in seconds.
        wait -- Time to long poll for messages, in seconds. Max is 30 seconds. Default 0.
        delete -- If true, do not put each message back on to the queue after reserving. Default false.
        """
        url = "queues/%s/reservations" % self.name
        qitems = {}
        if max is not None:
            qitems['n'] = max
        if timeout is not None:
            qitems['timeout'] = timeout
        if wait is not None:
            qitems['wait'] = wait
        if delete is not None:
            qitems['delete'] = delete
        body = json.dumps(qitems)

        response = self.client.post(url, body=body,
                                    headers={'Content-Type': 'application/json'})

        return response['body']


    def get_message_by_id(self, message_id):
        url = "queues/%s/messages/%s" % (self.name, message_id)
        response = self.client.get(url)
        return response['body']['message']

    def peek(self, max=None):
        url = "queues/%s/messages" % self.name
        if max is not None:
            url = "%s?n=%s" % (url, max)

        response = self.client.get(url)

        return response['body']

    def touch(self, message_id, reservation_id, timeout=None):
        """Touching a reserved message extends its timeout to the duration specified when the message was created.

        Arguments:
        message_id -- The ID of the message.
        reservation_id -- Reservation Id of the message.
        timeout -- Optional. The timeout in seconds after which new reservation will expire.
        """
        url = "queues/%s/messages/%s/touch" % (self.name, message_id)
        qitems = {'reservation_id': reservation_id}
        if timeout is not None:
            qitems['timeout'] = timeout
        body = json.dumps(qitems)

        response = self.client.post(url, body=body,
                                    headers={'Content-Type': 'application/json'})

        return response['body']

    def release(self, message_id, reservation_id, delay=0):
        """Release locked message after specified time. If there is no message with such id on the queue.

        Arguments:
        message_id -- The ID of the message.
        reservation_id -- Reservation Id of the message.
        delay -- The time after which the message will be released.
        """
        url = "queues/%s/messages/%s/release" % (self.name, message_id)
        body = {'reservation_id': reservation_id}
        if delay > 0:
            body['delay'] = delay
        body = json.dumps(body)

        response = self.client.post(url, body=body,
                                    headers={'Content-Type': 'application/json'})

        return response['body']

    def update(self, options=None):
        url = "queues/%s" % self.name

        body = json.dumps({})
        if options is not None:
            body = json.dumps({'queue': options})

        response = self.client.patch(url, body=body,
                                     headers={'Content-Type': 'application/json'})
        return response['body']['queue']

    def delete_queue(self):
        url = "queues/%s" % self.name

        response = self.client.delete(url)

        return response['body']

    def add_alerts(self, *alerts):
        body = json.dumps({'queue': {'alerts': alerts}})
        url = "queues/%s" % self.name

        response = self.client.patch(url=url, body=body,
                                     headers={'Content-Type': 'application/json'})
        return response['body']['queue']

    def update_alerts(self, *alerts):
        body = json.dumps({'queue': {'alerts': alerts}})
        url = "queues/%s" % self.name

        response = self.client.put(url=url, body=body,
                                   headers={'Content-Type': 'application/json'})
        return response['body']['queue']

    def remove_alerts(self, *alerts):
        url = "queues/%s/alerts" % self.name
        body = json.dumps({'queue':{'alerts': alerts}})
        response = self.client.delete(url, body=body, headers={"Content-Type":"application/json"})
        return response['body']

    def add_subscribers(self, *subscribers):
        url = "queues/%s/subscribers" % self.name
        body = json.dumps({'subscribers': subscribers})

        response = self.client.post(url, body=body,
                                    headers={'Content-Type': 'application/json'})

        return response['body']

    def remove_subscribers(self, *subscribers):
        url = "queues/%s/subscribers" % self.name
        body = json.dumps(self._prepare_subscribers(*subscribers))

        response = self.client.delete(url, body=body,
                                      headers={'Content-Type': 'application/json'})

        return response['body']

    def replace_subscribers(self, *subscribers):
        url = "queues/%s/subscribers" % self.name
        body = json.dumps({'subscribers': subscribers})

        response = self.client.put(url, body=body,
                                      headers={'Content-Type': 'application/json'})

        return response['body']

    def get_message_push_statuses(self, message_id):
        url = "queues/%s/messages/%s/subscribers" % (self.name, message_id)

        response = self.client.get(url)

        return response['body']

    def _prepare_alert_ids(self, *alert_ids):
        alerts = [{'id': id} for id in alert_ids]
        return {'alerts': alerts}

    def _prepare_subscribers(self, *subscribers):
        subscrs = [{'name': ss} for ss in subscribers]

        return {'subscribers': subscrs}

class IronMQ(object):
    NAME = 'iron_mq_python'
    VERSION = '0.7'
    API_VERSION = 3
    client = None
    name = None

    def __init__(self, name=None, **kwargs):
        """Prepare a configured instance of the API wrapper and return it.

        Keyword arguments are passed directly to iron_core_python; consult its
        documentation for a full list and possible values."""
        if name is not None:
            self.name = name
        kwargs['api_version'] = kwargs.get('api_version') or IronMQ.API_VERSION

        self.client = iron_core.IronClient(name=IronMQ.NAME,
                version=IronMQ.VERSION, product='iron_mq', **kwargs)


    def queues(self, page=None, per_page=None, previous=None, prefix=None):
        """Execute an HTTP request to get a list of queues and return it.

        Keyword arguments:
        page -- The 0-based page to get queues from. Defaults to None, which
                omits the parameter.
        """
        options = {}
        if page is not None:
            raise Exception('page param is deprecated!')
        if per_page is not None:
            options['per_page'] = per_page
        if previous is not None:
            options['previous'] = previous
        if prefix is not None:
            options['prefix'] = prefix

        query = urllib.urlencode(options)
        url = 'queues'
        if query != '':
            url = "%s?%s" % (url, query)
        result = self.client.get(url)

        return [queue['name'] for queue in result['body']['queues']]


    def queue(self, queue_name):
        """Returns Queue object.

        Arguments:
        queue_name -- The name of the queue.
        """
        return Queue(self, queue_name)


    def create_queue(self, queue_name, options=None):
        body = json.dumps({})
        if options is not None:
            body = json.dumps({'queue': options})
        url = "queues/%s" % queue_name
        response = self.client.put(url, body=body, headers={'Content-Type': 'application/json'})
        return response['body']['queue']


    def update_queue(self, queue_name, options=None):
        body = json.dumps({})
        if options is not None:
            body = json.dumps({'queue': options})
        url = "queues/%s" % queue_name
        response = self.client.patch(url, body=body,
                                       headers={'Content-Type': 'application/json'})
        return response['body']['queue']


    def _prepare_subscribers(self, *subscribers):
        subscrs = [{'url': ss} for ss in subscribers]
        return {'subscribers': subscrs}

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
