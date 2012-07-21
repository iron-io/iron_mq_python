from iron_mq import *
import unittest
import time


class TestIronMQ(unittest.TestCase):

    def setUp(self):
        self.mq = IronMQ()

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

    def test_clearQueue(self):
        queue = self.mq.postMessage("test_queue", ["%s" % time.time()])
        size = self.mq.getQueueDetails("test_queue")
        self.assertTrue(size["size"] > 0)
        self.mq.clearQueue("test_queue")
        new_size = self.mq.getQueueDetails("test_queue")
        self.assertEqual(new_size["size"], 0)


if __name__ == '__main__':
    unittest.main()
