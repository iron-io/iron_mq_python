# IronMQ For Python
import httplib

import urllib2
import socket
import ssl

import socket
import json
import ConfigParser


class HTTPSConnectionV3(httplib.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        try:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                    ssl_version=ssl.PROTOCOL_SSLv3)
        except ssl.SSLError, e:
            print "Trying SSLv3"
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                    ssl_version=ssl.PROTOCOL_SSLv23)


class HTTPSHandlerV3(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSConnectionV3, req)


urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))


class RequestWithMethod(urllib2.Request):
    def __init__(self, method, url, data=None, headers={},
            origin_req_host=None, unverifiable=False):
        self._method = method
        urllib2.Request.__init__(self, url, data, headers,
                origin_req_host, unverifiable)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib2.Request.get_method(self)


class IllegalArgumentException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class IronMQ:
    DEFAULT_HOST = "mq-aws-us-east-1.iron.io"
    USER_AGENT = "IronMQ Python v0.3"

    __headers = {
        "Accept": "application/json",
        "User-Agent": "IronMQ Python v0.3",
    }

    def __init__(self, token=None, project_id=None, host=DEFAULT_HOST,
            port=443, version=1, protocol='https', config=None,
            app_engine=False):
        """Prepare a configured instance of the API wrapper and return it.

        Keyword arguments:
        token -- An API token found on http://hud.iron.io. Defaults to None.
        project_id -- The ID for the project, found on http://hud.iron.io
        host -- The hostname of the API server.
                Defaults to mq-aws-us-east-1.iron.io.
        port -- The port of the API server. Defaults to 443.
        version -- The API version to use. Defaults to 1.
        protocol -- The protocol to use. Defaults to https.
        config -- The config file to draw config values from. Defaults to None.
        app_engine -- Deprecated; does nothing
        """
        self.token = token
        self.version = version
        self.project_id = project_id
        self.protocol = protocol
        self.host = host
        self.port = port
        self.version = version
        if config is not None:
            config_file = ConfigParser.RawConfigParser()
            config_file.read(config)
            try:
                self.token = config_file.get("IronMQ", "token")
            except ConfigParser.NoOptionError:
                self.token = token
            try:
                self.project_id = config_file.get("IronMQ", "project_id")
            except ConfigParser.NoOptionError:
                self.project_id = project_id
            try:
                self.host = config_file.get("IronMQ", "host")
            except ConfigParser.NoOptionError:
                self.host = host
            try:
                self.port = config_file.get("IronMQ", "port")
            except ConfigParser.NoOptionError:
                self.port = port
            try:
                self.version = config_file.get("IronMQ", "version")
            except ConfigParser.NoOptionError:
                self.version = version
            try:
                self.protocol = config_file.get("IronMQ", "protocol")
            except ConfigParser.NoOptionError:
                self.protocol = protocol
        if self.token is None or self.project_id is None:
            raise IllegalArgumentException("Both token and project_id must \
                    have a value")
        self.url = "%s://%s:%s/%s/" % (self.protocol, self.host, self.port,
                self.version)

    def __req(self, url, method, body=None, headers=None):
        if headers is None:
            headers = IronMQ.__headers
        else:
            headers = dict(headers.items() + IronMQ.__headers.items())
        if self.protocol == "http":
            conn = httplib.HTTPConnection(self.host, self.port)
            conn.request(method, url, body, headers)
            resp = conn.getresponse()
        elif self.protocol == "https":
            #conn = httplib.HTTPSConnection(self.host, self.port)
            req = RequestWithMethod(method, url, body, headers)
            resp = urllib2.urlopen(req)
        body = resp.read()
        if self.protocol == "http":
            conn.close()
        return body

    def __get(self, url, headers=None):
        """Execute an HTTP GET request and return the result.

        Keyword arguments:
        url -- The url to execute the request against. (Required)
        headers -- A dict of headers to merge with IronMQ.__headers and send
                   with the request.
        """
        return self.__req(url, "GET", headers=headers)

    def __post(self, url, payload=None, headers=None):
        """Execute an HTTP POST request and return the result.

        Keyword arguments:
        url -- The url to execute the request against. (Required)
        payload -- A dict of key-value form data to send with the
                   request. Will be urlencoded.
        headers -- A dict of headers to merge with IronMQ.__headers and send
                   with the request.
        """
        if headers is None:
            headers = {"Content-Type": "application/json"}
        return self.__req(url, "POST", body=payload, headers=headers)

    def __delete(self, url, headers=None):
        """Execute an HTTP DELETE request and return the result.

        Keyword arguments:
        url -- The url to execute the request against. (Required)
        headers -- A dict of headers to merge with IronMQ.__headers and send
                   with the request.
        """
        return self.__req(url, "DELETE", headers=headers)

    def getQueues(self, page=None, project_id=None):
        """Execute an HTTP request to get a list of queues and return it.

        Keyword arguments:
        project_id -- The project ID to get queues from. Defaults to the
                      project ID set when initialising the wrapper.
        page -- The 0-based page to get queues from. Defaults to None, which
                omits the parameter.
        """
        if project_id is None:
            project_id = self.project_id
        pageForURL = ""
        if page is not None:
            pageForURL = "&page=%s" % page
        url = "%sprojects/%s/queues?oauth=%s%s" % (self.url, project_id,
                self.token, pageForURL)
        body = self.__get(url)
        queues = json.loads(body)
        return queues

    def getQueueDetails(self, queue_name, project_id=""):
        """Execute an HTTP request to get details on a specific queue, and
        return it.

        Keyword arguments:
        queue_name -- The name of the queue to get the details of. (Required)
        project_id -- The ID of the project the queue belongs to. Defaults to
                      the project ID set when initialising the wrapper.
        """
        if project_id == "":
            project_id = self.project_id
        url = "%sprojects/%s/queues/%s?oauth=%s" % (self.url, project_id,
                queue_name, self.token)
        body = self.__get(url)
        queue = json.loads(body)
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
        if project_id is None:
            project_id = self.project_id
        url = "%sprojects/%s/queues/%s/messages/%s?oauth=%s" % (self.url,
                project_id, queue_name, message_id, self.token)
        body = self.__delete(url)
        return json.loads(body)

    def postMessage(self, queue_name, messages=[], project_id=None):
        """Executes an HTTP request to create message on the queue.

        Keyword arguments:
        queue_name -- The name of the queue to add the message to. (Required)
        messages -- An array of messages to be added to the queue.
                    Defaults to [].
        project_id -- The ID of the project the queue is under. Defaults to
                      the project ID set when the wrapper was initialised.
        """
        if project_id is None:
            project_id = self.project_id
        url = "%sprojects/%s/queues/%s/messages?oauth=%s" % (self.url,
                project_id, queue_name, self.token)
        msgs = [{'body':msg} if isinstance(msg, basestring) else msg
                for msg in messages]
        data = json.dumps({"messages": msgs})
        dataLen = len(data)

        s = self.__post(url=url, payload=data)

        ret = json.loads(s)
        return ret

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
        if project_id is None:
            project_id = self.project_id
        n = ""
        if max is not None:
            n = "&n=%s" % max
        url = "%sprojects/%s/queues/%s/messages?oauth=%s%s" % (self.url,
                project_id, queue_name, self.token, n)
        body = self.__get(url)
        return json.loads(body)

    def clearQueue(self, queue_name, project_id=None):
        """Executes an HTTP request to clear all contents of a queue.

        Keyword arguments:
        queue_name -- The name of the queue a messages are being cleared from.
                      (Required)
        project_id -- The ID of the project that contains the queue that is
                      being cleared. Defaults to the project ID set when the
                      wrapper was initialised.
        """
        if project_id is None:
            project_id = self.project_id

        url = "%sprojects/%s/queues/%s/clear?oauth=%s" % (self.url, project_id,
                queue_name, self.token)
        body = self.__post(url)
        return json.loads(body)
