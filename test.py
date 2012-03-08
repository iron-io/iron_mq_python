from iron_mq import *
import unittest
import ConfigParser
import time


class TestIronMQ(unittest.TestCase):

    def setUp(self):
        config = ConfigParser.RawConfigParser()
        config.read('config.ini')
        self.token = config.get("IronMQ", "token")
        self.project_id = config.get("IronMQ", "project_id")

        self.mq = IronMQ(token=self.token, project_id=self.project_id)

    def test_headers(self):
        self.assertEqual(IronMQ._IronMQ__headers['Accept'], "application/json")
        self.assertEqual(IronMQ._IronMQ__headers['User-Agent'],
                "IronMQ Python v0.3")

    def test_protocols(self):
        mq = IronMQ(token=self.token, project_id=self.project_id)
        if mq.protocol == "http":
            self.assertEqual(mq.port, 80)
        elif mq.protocol == "https":
            self.assertEqual(mq.port, 443)
        self.assertTrue(mq.protocol in ["http", "https"])

    def test_postMessage(self):
        queue = self.mq.getQueueDetails("test_queue")
        self.mq.postMessage("test_queue", ["test message"])
        queue2 = self.mq.getQueueDetails("test_queue")
        self.assertEqual(queue["size"], (queue2["size"] - 1))

    def test_getMessage(self):
        msg = "%s" % time.time()
        self.mq.postMessage("test_queue", [msg])
        message = self.mq.getMessage("test_queue")
        message = "%s" % message["messages"][0]["body"]
        self.assertEqual(msg, message)

    def test_deleteMessage(self):
        queue = self.mq.getQueueDetails("test_queue")
        msg = self.mq.postMessage("test_queue", ["test"])
        queue2 = self.mq.getQueueDetails("test_queue")
        self.mq.deleteMessage("test_queue", msg["ids"][0])
        queue3 = self.mq.getQueueDetails("test_queue")
        self.assertEqual(queue["size"], (queue2["size"] - 1))
        self.assertEqual(queue["size"], queue3["size"])

if __name__ == '__main__':
    unittest.main()
