import asyncio
from typing import Callable

import discord.utils

import common.logging


class QueueWorker:
    def __init__(self, delay: float = 0.0):
        """
        A worker that processes tasks from a queue.
        Errors are tracked and the delay between tasks is increased exponentially if consecutive errors occur.

        :param delay: The time in seconds to wait between tasks
        """
        self._queue = asyncio.Queue()
        self._error_count = 0
        self._delay = delay
        self._task: asyncio.Task = None
        self._delayed_tasks = set()

    async def _worker(self):
        while True:
            try:
                await asyncio.sleep((2 ** self._error_count) - 1)
                task, args, kwargs = await self._queue.get()

                try:
                    await discord.utils.maybe_coroutine(task, *args, **kwargs)
                finally:
                    self._queue.task_done()

                if self._error_count > 0:
                    self._error_count -= 1

                await asyncio.sleep(self._delay)
            except (KeyboardInterrupt, SystemExit, asyncio.CancelledError) as e:
                raise e
            except Exception as ex:
                common.logging.error(exc_info=ex)
                if self._error_count < 12:
                    self._error_count += 1

    def put(self, f: Callable, *args, **kwargs):
        """
        Add a task to the queue for execution.

        :param f: The function to call. If the function is a coroutine, it will be awaited.
        :param args: The arguments to pass to the function.
        :param kwargs: The keyword arguments to pass to the function.
        """
        self._queue.put_nowait((f, args, kwargs))

    async def _put_delayed(self, f: Callable, delay: float, *args, **kwargs):
        await asyncio.sleep(delay)
        self.put(f, *args, **kwargs)

    def put_delayed(self, f: Callable, delay: float, *args, **kwargs):
        """
        Add a task to the queue for execution after a delay.

        :param f: The function to call. If the function is a coroutine, it will be awaited.
        :param delay: The time in seconds to wait before executing the task.
        :param args: The arguments to pass to the function.
        :param kwargs: The keyword arguments to pass to the function.
        """
        task = asyncio.create_task(self._put_delayed(f, delay, *args, **kwargs))

        # Keep a reference to the task to prevent it from being garbage collected
        self._delayed_tasks.add(task)
        task.add_done_callback(self._delayed_tasks.discard)

    async def join(self):
        """
        Block until all items in the queue have been gotten and processed.
        The count of unfinished tasks goes up whenever an item is added to the queue.
        The count goes down whenever a task is completed.
        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        await self._queue.join()

    def qsize(self):
        """
        Number of items in the queue.
        """
        return self._queue.qsize()

    def empty(self):
        """
        Return True if the queue is empty, False otherwise.
        """
        return self._queue.empty()

    @property
    def started(self):
        """
        Return True if the worker is running, False otherwise.
        """
        return self._task is not None

    def start(self):
        """
        Start the worker.
        """
        if self._task is not None:
            raise RuntimeError("Worker already running")
        self._task = asyncio.create_task(self._worker())

    def stop(self):
        """
        Stop the worker.
        """
        if self._task is not None:
            self._task.cancel()
        self._error_count = 0
        self._task = None
