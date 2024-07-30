import asyncio


class DynamicSemaphore:
    def __init__(self, initial_count):
        self._semaphore = asyncio.Semaphore(initial_count)
        self._max_count = initial_count
        self._lock = asyncio.Lock()

    async def acquire(self):
        await self._semaphore.acquire()

    def release(self):
        self._semaphore.release()

    async def update_max_count(self, new_max_count):
        async with self._lock:
            diff = new_max_count - self._max_count
            if diff > 0:
                for _ in range(diff):
                    self._semaphore.release()
            elif diff < 0:
                for _ in range(-diff):
                    await self._semaphore.acquire()
            self._max_count = new_max_count

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
