from iron_mq import *
import unittest
import ConfigParser
import time


class TestIronMQ(unittest.TestCase):

    def setUp(self):
        config = ConfigParser.RawConfigParser()
        config.read('config.ini')
        self.token = config.get("IronMQ", "token")
        self.host = config.get("IronMQ", "host")
        self.port = config.get("IronMQ", "port")
        self.version = config.get("IronMQ", "version")
        self.project_id = config.get("IronMQ", "project_id")

        self.mq = IronMQ(token=self.token, host=self.host,
            port=self.port, version=self.version, project_id=self.project_id)

    def test_headers(self):
        self.assertEqual(self.mq.headers['Accept'], "application/json")
        self.assertEqual(self.mq.headers['Accept-Encoding'],
                "gzip, deflate")
        self.assertEqual(self.mq.headers['User-Agent'],
                "IronMQ Python v0.3")

    def test_postMessage(self):
        queue = self.mq.getQueueDetails("test_q")
        self.mq.postMessage("test_q", ["test message"])
        queue2 = self.mq.getQueueDetails("test_q")
        self.assertEqual(queue["size"], (queue2["size"] - 1))

    def test_getMessage(self):
        msg = "%s" % time.time()
        self.mq.postMessage(msg, [msg])
        message = self.mq.getMessage(msg)
        message = "%s" % message["messages"][0]["body"]
        self.assertEqual(msg, message)

    def test_deleteMessage(self):
        queue = self.mq.getQueueDetails("test_q")
        msg = self.mq.postMessage("test_q", ["test"])
        queue2 = self.mq.getQueueDetails("test_q")
        self.mq.deleteMessage("test_q", msg["ids"][0])
        queue3 = self.mq.getQueueDetails("test_q")
        self.assertEqual(queue["size"], (queue2["size"] - 1))
        self.assertEqual(queue["size"], queue3["size"])

if __name__ == '__main__':
    unittest.main()
