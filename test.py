from iron_mq import *
import unittest
import random
import time


class TestIronMQ(unittest.TestCase):

    def setUp(self):
        self.mq = IronMQ()
        self.random_number = str(int(random.random() * 10**10))

    def test_postMessage(self):
        q = self.mq.queue("test_queue")
        old_size = q.size()
        q.post("test message")
        self.assertEqual(old_size, q.size() - 1)

    def test_addAlerts(self):
        q = self.mq.queue("test_queue" + self.random_number)
        result = q.add_alerts({'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'})
        self.assertEqual(result['msg'], 'Updated')

    def test_updateAlerts(self):
        q = self.mq.queue("test_queue")
        result = q.update_alerts({'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'})
        self.assertEqual(result['msg'], 'Updated')

    def test_infoShouldReturnAlerts(self):
        q = self.mq.queue("test_queue" + self.random_number)
        q.add_alerts({'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'})
        info = q.info()
        self.assertTrue('alerts' in info)
        self.assertEqual(len(info['alerts']), 1)

    def test_removeAlerts(self):
        q = self.mq.queue("test_queue" + self.random_number)
        q.add_alerts({'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'}, {'type': 'fixed', 'direction': 'asc', 'trigger': 10000, 'queue': 'a_q'}, {'type': 'progressive', 'direction': 'asc', 'trigger': 500, 'queue': 'a_q'})
        alerts = [alert['id'] for alert in q.info()['alerts']][0:2]
        last_alert = q.info()['alerts'][2]
        result = q.remove_alerts(*alerts)
        self.assertEqual(result['msg'], 'Deleted')
        self.assertEqual(len(q.info()['alerts']), 1)
        self.assertEqual(q.info()['alerts'][0]['id'], last_alert['id'])

    def test_removeAlert(self):
        q = self.mq.queue("test_queue" + self.random_number)
        q.add_alerts({'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'}, {'type': 'fixed', 'direction': 'asc', 'trigger': 10000, 'queue': 'a_q'})
        result = q.remove_alert(q.info()['alerts'][0]['id'])
        self.assertEqual(result['msg'], 'Deleted')
        self.assertEqual(len(q.info()['alerts']), 1)

    def test_getMessage(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.post(msg)
        message = q.get()
        message = "%s" % message["messages"][0]["body"]
        self.assertEqual(msg, message)

    def test_getMessageTimeout(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        q.post(msg)
        message = q.get(timeout=180)
        message = "%s" % message["messages"][0]["body"]
        self.assertEqual(msg, message)
        time.sleep(120)
        m2 = q.get()
        self.assertEqual(0, len(m2["messages"]))
        time.sleep(120)
        m3 = q.get()
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

    def test_deprecated(self):
        self.assertEqual(self.mq.queues(), self.mq.getQueues())

        name = 'test_queue'
        q = self.mq.queue(name)

        self.assertEqual('Cleared', self.mq.clearQueue(name)['msg'])

        self.assertEqual(0, q.size())

        info = self.mq.getQueueDetails(name)
        self.assertEqual(q.info(), info)

        msg_id = self.mq.postMessage(name, ['hello mq'])['ids'][0]

        resp = self.mq.getMessage(name)
        self.assertEqual(msg_id, resp['messages'][-1]['id'])

        self.assertEqual('Deleted', self.mq.deleteMessage(name, msg_id)['msg'])

    def test_postAndDeleteMultipleMessages(self):
        q = self.mq.queue("test_queue")
        old_size = q.size()
        msg = q.post("more", "and more")
        self.assertEqual(old_size, q.size() - 2)

        q.delete_multiple(msg["ids"][0],msg["ids"][1])
        self.assertEqual(old_size, q.size())

    def test_getMessageById(self):
        body = "%s" % time.time()
        q = self.mq.queue("test_queue")
        response_post = q.post(body)
        message = q.get_message_by_id(response_post["ids"][0])
        self.assertEqual(body, message["body"])

if __name__ == '__main__':
    unittest.main()
