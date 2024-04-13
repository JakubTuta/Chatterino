import queue
import threading
import time

from firebase.messagesStore import createMessage


class MessageBuffer:
    def __init__(self):
        self.q = queue.Queue()

        t_readQueue = threading.Thread(target=self.readQueue)
        t_readQueue.start()

    def push(self, item):
        self.q.put(item)

    def readQueue(self):
        while True:
            if not self.q.empty():
                item = self.q.get()
                createMessage(item)
            time.sleep(1)
