from iron_mq import *
import unittest
import random
import time


class TestIronMQ(unittest.TestCase):
    def setUp(self):
        self.mq =   IronMQ(host="mq-v3-aws-us-east-1.iron.io",
            project_id = "5433ac2e37c0d2000a000015",
            token = "WUmafTN45PbOTu1AUedJ",
            protocol = "https", port = 443, api_version = 3,
            config_file = None)
        self.random_number = str(int(random.random() * 10 ** 10))

    def test_postMessage(self):
        q = self.mq.queue("test_queue")
        old_size = q.size()
        q.post("test message")
        self.assertEqual(old_size, q.size() - 1)

    def test_addAlerts(self):
        q = self.mq.queue("test_queue")
        q.clear()
        fixed_alert = [{'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'}]
        response = q.add_alerts(*fixed_alert)
        self.assertTrue("alerts" in response)


    def test_infoShouldReturnAlerts(self):
        q = self.mq.queue("test_queue")
        q.clear()
        fixed_alert = [{'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'}]
        q.add_alerts(*fixed_alert)
        info = q.info()
        self.assertTrue('alerts' in info)
        self.assertEqual(len(info['alerts']), 1)

    def test_removeAlerts(self):
        q = self.mq.queue("test_queue")
        q.clear()
        fixed_alerts = [{'type': 'fixed', 'direction': 'desc', 'trigger': 1000, 'queue': 'a_q'},
                        {'type': 'fixed', 'direction': 'asc', 'trigger': 10000, 'queue': 'a_q'},
                        {'type': 'progressive', 'direction': 'asc', 'trigger': 500, 'queue': 'a_q'}]
        response = q.add_alerts(fixed_alerts)
        self.assertEqual(len(response["alerts"]), len(fixed_alerts))
        result = q.remove_alerts()
        self.assertEqual(len(result["alerts"]), 1)

    def test_touchMessage(self):
        msg = "Test message %s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        id = q.post(msg)
        message = q.reserve()
        response = q.touch(message[0]["id"], message[0]["reservation_id"])
        self.assertEqual("Touched", response["msg"])

    def test_releaseMessage(self):
        msg = "Test message %s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        id = q.post(msg)
        message = q.reserve()
        response = q.release(message_id=message[0]["id"], reservation_id=message[0]["reservation_id"])
        self.assertEqual("Released", response["msg"])

    def test_addSubscribers(self):
        queue_name = "test_queue%s" % time.time()
        subscribers = [{'name': 'first', 'url': 'http://first.endpoint.xx/process' }]
        self.mq.create_queue(queue_name, {'push': {'subscribers': subscribers}} )
        q = self.mq.queue(queue_name)
        response = q.add_subscribers(*[{'name': 'second', 'url': 'http://first.endpoint.xx/process'}])
        self.assertEqual(response["msg"], "Updated")
        info = q.info()
        self.assertEqual(2, len(info['push']['subscribers']))

    def test_removeSubscribers(self):
        queue_name = "test_queue%s" % time.time()
        subscribers = [{'name': 'first',
                        'url': 'http://first.endpoint.xx/process'},
                       {'name': 'second',
                        'url': 'http://second.endpoint.xx/process'}]
        self.mq.create_queue(queue_name, {'push': {'subscribers': subscribers}} )
        q = self.mq.queue(queue_name)
        response = q.remove_subscribers(*['first'])
        self.assertEqual(response["msg"], "Updated")
        info = q.info()
        self.assertEqual(1, len(info['push']['subscribers']))

    def test_getMessage(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        q.post(msg)
        message = q.get()
        message = "%s" % message[0]["body"]
        self.assertEqual(msg, message)

    def test_reserveMessages(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        ids = q.post(msg + str(0), msg + str(1), msg + str(2))
        messages = q.reserve(3)

        for idx, val in enumerate(messages):
            self.assertEqual(msg + str(idx), val["body"])
            self.assertEqual(ids["ids"][idx], val["id"])
            self.assertTrue(len(val["reservation_id"]) > 0)
            self.assertEqual(val["reserved_count"], 1)

    def test_reserveMessage(self):
         msg = "Test message %s" % time.time()
         q = self.mq.queue("test_queue")
         q.clear()
         id = q.post(msg)
         message = q.reserve()
         self.assertEqual(msg, message[0]["body"])
         self.assertEqual(id["ids"][0], message[0]["id"])


    def test_getMessageTimeout(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        q.post(msg)
        message = q.get(timeout=180)
        message = "%s" % message[0]["body"]
        self.assertEqual(msg, message)
        time.sleep(120)
        m2 = q.get()
        self.assertEqual(0, len(m2))
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

    def test_deleteReservedMessage(self):
        msg = "%s" % time.time()
        q = self.mq.queue("test_queue")
        q.clear()
        id = q.post(msg)
        message = q.reserve(1, 60)
        self.assertEqual(1, q.size())
        reservation_id = message[0]["reservation_id"]
        q.delete(id["ids"][0], reservation_id)
        self.assertEqual(0, q.size())

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
        q.clear()

        self.assertEqual('Cleared', self.mq.clearQueue(name)['msg'])

        self.assertEqual(0, q.size())

        info = self.mq.getQueueDetails(name)
        self.assertEqual(q.info(), info)

        msg_id = self.mq.postMessage(name, ['hello mq'])['ids'][0]

        resp = self.mq.getMessage(name)
        self.assertEqual(msg_id, resp[-1]['id'])

    def test_postAndDeleteMultipleMessages(self):
        q = self.mq.queue("test_queue")
        q.clear()
        old_size = q.size()
        ids = q.post("more", "and more")["ids"]
        self.assertEqual(old_size, q.size() - 2)
        q.delete_multiple(ids=ids)
        self.assertEqual(old_size, q.size())

    def test_deleteMultipleReservedMessages(self):
        q = self.mq.queue("test_queue")
        q.clear()
        old_size = q.size()
        q.post("more", "and more")
        messages = q.reserve(2, 60)
        self.assertEqual(old_size, q.size() - 2)
        q.delete_multiple(messages=messages)
        self.assertEqual(old_size, q.size())

    def test_getMessageById(self):
        body = "%s" % time.time()
        q = self.mq.queue("test_queue")
        response_post = q.post(body)
        message = q.get_message_by_id(response_post["ids"][0])
        self.assertEqual(body, message["body"])

    def test_peekMessages(self):
        q = self.mq.queue("test_queue")
        q.clear()
        q.post("more", "and more")
        response = q.peek(2)
        self.assertEqual(2, len(response))


if __name__ == '__main__':
    unittest.main()
