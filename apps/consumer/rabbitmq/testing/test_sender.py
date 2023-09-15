import unittest
import pytest
from testing.test_app import initialize_app
from concurrent.futures import ThreadPoolExecutor


# import pydevd_pycharm
# pydevd_pycharm.settrace('host.docker.internal', port=21000, stdoutToServer=True, stderrToServer=True)

@pytest.mark.wm_light
class RabitMQSenderTests(unittest.TestCase):
    def setUp(self):
        self.app = initialize_app()
        self.client = self.app.test_client()

    def tearDown(self):
        pass

    def send_message(self, msg):
        with self.app.app_context():
            from apps.consumer.rabbitmq.queue_sender import QueueSender
            from utils.func import log

            queue_sender = QueueSender(logger=log)
            queue_sender.send(msg)
            log('Queue sent: {}'.format(msg))

    def test_send_messages(self):
        messages = [
            {
                "user_id": "1891",
                "cl_id": "64de058acc909",
                "req_id": 636689817,
                "entities": [{"id": "1137", "type": "node", "action": "update"}],
                "ro": {"ips": ["172.18.0.1"], "vis_id": "7d34c16b493de1f22794642565a04fbd"}
            }
            for _ in range(100)
        ]

        num_threads = 3
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            executor.map(self.send_message, messages)


if __name__ == "__main__":
    unittest.main()
