from iron_mq import *
import unittest
import time


class TestIronMQ(unittest.TestCase):

    def setUp(self):
        self.mq = IronMQ()

    def test_queueList(self):
        queue = self.mq.queue('test_queue')
        queue.post('test message')

        qlist = self.mq.queues(instantiate=True)
        self.assertTrue(len(qlist) > 0, 'queue list is empty')

        test_queue_present = False
        qnames = [q.name for q in qlist]
        self.assertTrue('test_queue' in qnames, 'queue named "test_queue" is not present in list: %s' % qnames)

        self.delete_queue(queue)
        queue.post('test message')

        qlist = self.mq.queues(instantiate=False)
        self.assertTrue('test_queue' in qlist, 'queue named "test_queue" is not present in list: %s' % qlist)


    def test_postMessage(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post('test message')
        size = queue.size()

        queue.post("test message")
        self.assertEqual(size, queue.size() - 1)


    def test_getMessage(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post('test message')

        message = queue.get()
        self.assertEqual('test message', message.body)


    def test_deleteMessage(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post('test message')
        size = queue.size()

        queue.post('test message')
        self.assertEqual(size, queue.size() - 1)

        msg = queue.get()
        msg.delete()
        self.assertEqual(size, queue.size())


    def test_clearQueue(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post('test message')

        queue.post("%s" % time.time())
        self.assertTrue(queue.size() > 0)

        queue.clear()
        self.assertEqual(queue.size(), 0)


    def test_messageTimeout(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post('my message', timeout=30)

        msg1 = queue.get()
        self.assertEqual(msg1.body, 'my message')

        time.sleep(10)
        msg2 = queue.get()
        self.assertIsNone(msg2, 'expects message is not available')

        time.sleep(15)
        msg2 = queue.get()
        self.assertIsNone(msg2, 'expects message is not available')

        time.sleep(10)
        msg2 = queue.get()
        self.assertIsNotNone(msg2, 'expects message is available after timeout')
        self.assertEqual(msg1.id, msg2.id, 'expected msg ID is "%s", but got "%s"' % (msg1.id, msg2.id))


    def test_messageDelay(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post('my message', delay=5)

        msg = queue.get()
        self.assertIsNone(msg, 'expects message is not available')

        time.sleep(7)

        msg = queue.get()
        self.assertIsNotNone(msg, 'expects message is available after delay')
        self.assertEqual('my message', msg.body,
                         'expected message body is "my message", but got "%s"' % msg.body)


    def test_batchPost(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        messages = ['first', 'second', 'third']
        queue.post(*messages)
        self.assertEqual(3, queue.size())

        for message in messages:
            msg = queue.get()
            self.assertEqual(message, msg.body,
                             'expected body is "%s", but got "%s"' % (message, msg.body))


    def test_messagePeek(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        messages = ['first', 'second', 'third']
        queue.post(*messages)

        msg1 = queue.peek()
        msg2 = queue.peek()
        self.assertEqual(msg1.id, msg2.id,
                         'messages IDs must be equal, but got "%s" & "%s"' % (msg1.id, msg2.id))
        self.assertEqual(msg1.body, msg2.body,
                         'messages bodies must be equal, but got "%s" & "%s"' % (msg1.body, msg2.body))

        msg = queue.get()
        self.assertEqual(msg.id, msg1.id,
                         'messages IDs must be equal, but got "%s" & "%s"' % (msg.id, msg1.id))
        self.assertEqual(msg.body, msg1.body,
                         'messages bodies must be equal, but got "%s" & "%s"' % (msg.body, msg1.body))

        msg1 = queue.peek()
        msg2 = queue.peek()
        self.assertNotEqual(msg.id, msg1.id, 'messages IDs must not be equal')
        self.assertNotEqual(msg.body, msg1.body, 'messages bodies must not be equal')
        self.assertEqual(msg1.id, msg2.id,
                         'messages IDs must be equal, but got "%s" & "%s"' % (msg1.id, msg2.id))
        self.assertEqual(msg1.body, msg2.body,
                         'messages bodies must be equal, but got "%s" & "%s"' % (msg1.body, msg2.body))


    def test_messageTouch(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        messages = ['first', 'second', 'third']
        queue.post(*messages, timeout=30)

        msg = queue.get()
        self.assertIsNotNone(msg)

        time.sleep(15)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(2, len(msgs), 'expected list with 2 messages, but got %s' % len(msgs))

        time.sleep(20)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(3, len(msgs), 'expected list with 3 messages, but got %s' % len(msgs))
        self.assertEqual(msg.id, msgs[2].id, "released message must be at the end of the queue")

        msg = queue.get()
        self.assertIsNotNone(msg)

        time.sleep(15)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(2, len(msgs), 'expected list with 2 messages, but got %s' % len(msgs))

        msg.touch() # for more 30 seconds

        time.sleep(20)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(2, len(msgs), 'expected list with 2 messages, but got %s' % len(msgs))

        time.sleep(15)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(3, len(msgs), 'expected list with 3 messages, but got %s' % len(msgs))
        self.assertEqual(msg.id, msgs[2].id, "released message must be at the end of the queue")


    def test_messageRelease(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        messages = ['first', 'second', 'third']
        queue.post(*messages)

        msg = queue.get()
        msg.release(delay=5)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(2, len(msgs), 'expected list with 2 messages, but got %s' % len(msgs))

        time.sleep(7)
        msgs = queue.peek(count=3)
        self.assertIsInstance(msgs, list, 'list of messages expected')
        self.assertEqual(3, len(msgs), 'expected list with 3 messages, but got %s' % len(msgs))


    def test_deleteQueue(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)


    def test_backwardCompatibility(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue.post({'body': 'backward test #1'},
                   {'body': 'backward test #2'},
                   raw=True)
        self.assertEqual(2, queue.size(), 'queue size must be 2 (backward compatibility)')

        msgs = queue.get(max=2, instantiate=False)
        self.assertIsInstance(msgs, dict, 'dict response expected (backward compatibility)')

        for msg in msgs['messages']:
            queue.delete(msg['id'])

        self.delete_queue(queue)


    def test_queueInfo(self):
        queue = self.mq.queue('test_queue')
        self.delete_queue(queue)

        queue_info = queue.info()
        self.assertIsInstance(queue_info, dict, 'queue info must be dict')
        self.assertEqual('test_queue', queue_info['name'], 'queue name must be "test_queue"')
        self.assertEqual(0, queue_info['size'], 'queue size must be 0')
        self.assertEqual(0, queue_info['total_messages'], 'queue total messages must be 0')
        self.assertIsNone(queue_info['id'], 'queue ID must be None')
        self.assertIsNone(queue_info['push_type'], 'queue push type must be None')

        messages = ['first', 'second', 'third']
        queue.post(*messages)

        queue_info = queue.info()
        self.assertIsInstance(queue_info, dict, 'queue info must be dict')
        self.assertEqual('test_queue', queue_info['name'], 'queue name must be "test_queue"')
        self.assertEqual(3, queue_info['size'], 'queue size must be 0')
        self.assertEqual(3, queue_info['total_messages'], 'queue total messages must be 0')
        self.assertIsNotNone(queue_info['id'], 'queue ID must not be None')
        self.assertIsNone(queue_info['push_type'], 'queue push type must be None')

        self.delete_queue(queue)


    def delete_queue(self, queue):
        queue.delete()
        self.assertTrue(queue.is_new(), 'queue is not deleted')


if __name__ == '__main__':
    unittest.main()
