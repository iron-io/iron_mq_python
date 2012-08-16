from iron_mq import *
import unittest
import time


class TestIronMQ(unittest.TestCase):

    def setUp(self):
        self.mq = IronMQ()

    def test_postMessage(self):
        q = self.mq.queue("test_queue")
        old_size = q.size()
        q.post("test message")
        self.assertEqual(old_size, q.size() - 1)

    def test_getMessage(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.post(msg)
        message = q.get()
        message = "%s" % message["messages"][0]["body"]
        self.assertEqual(msg, message)

    def test_deleteMessage(self):
        q = self.mq.queue("test_queue")
        size = q.size()

        msg = q.post("test")
        self.assertEqual(size, q.size() - 1)

        q.delete(msg["ids"][0])
        self.assertEqual(size, q.size())

    def test_clearQueue(self):
        q = self.mq.queue("test_queue")

        q.post("%s" % time.time())
        self.assertTrue(q.size() > 0)

        q.clear()
        self.assertEqual(q.size(), 0)


if __name__ == '__main__':
    unittest.main()
