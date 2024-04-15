import queue
import threading
import time

import firebase_functions.messagesStore as message_store


class MessageBuffer:
    def __init__(self):
        self.q = queue.Queue()

        t_read_queue = threading.Thread(target=self.__read_queue)
        t_read_queue.start()

    def push(self, item):
        self.q.put(item)

    def __read_queue(self):
        while True:
            if not self.q.empty():
                item = self.q.get()
                message_store.create_message(item)
            time.sleep(1)
