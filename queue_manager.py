import asyncio
import time
from collections import deque

class QueueManager:
    def __init__(self):
        self.queue = deque()
        self.last_request_time = time.time()
        self.request_count = 0
        self.lock = asyncio.Lock()

    async def add_to_queue(self, coroutine):
        await self.lock.acquire()
        try:
            future = asyncio.Future()
            self.queue.append((coroutine, future))
            await self.process_queue()
            return await future
        finally:
            self.lock.release()

    async def process_queue(self):
        while self.queue:
            current_time = time.time()
            if current_time - self.last_request_time >= 10:
                self.last_request_time = current_time
                self.request_count = 0

            if self.request_count < 2:
                coroutine, future = self.queue.popleft()
                self.request_count += 1
                try:
                    result = await coroutine
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
            else:
                await asyncio.sleep(0.5)  # Wait a bit before checking again

    async def run_coroutine(self, coroutine):
        return await self.add_to_queue(coroutine)

# Create a global instance of QueueManager
queue_manager = QueueManager()

class FluxQueueManager(QueueManager):
    def __init__(self):
        super().__init__()
        self.max_concurrent = 1  # Adjust based on Flux API limitations

flux_queue_manager = FluxQueueManager()

class FluxQueueManager(QueueManager):
    def __init__(self):
        super().__init__()
        self.max_concurrent = 1

    async def process_queue(self):
        while self.queue:
            if len([task for task in asyncio.all_tasks() if task.get_name().startswith('flux_task')]) < self.max_concurrent:
                coroutine, future = self.queue.popleft()
                task = asyncio.create_task(coroutine(), name=f'flux_task_{id(coroutine)}')
                task.add_done_callback(lambda t: self._task_done(t, future))
            else:
                await asyncio.sleep(0.5)

    def _task_done(self, task, future):
        try:
            result = task.result()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            debug(f"Flux task {task.get_name()} completed. Queue size: {len(self.queue)}")

flux_queue_manager = FluxQueueManager()
