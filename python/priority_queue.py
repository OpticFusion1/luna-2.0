import asyncio
from execute_action import execute_action

async def priority_queue_loop(container):
  while True:
    Prompt = container.priority_queue.dequeue() # this dequeue is thread-safe and blocking.
    execute_action(container, Prompt)

def priority_queue_loop_run(container):
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(priority_queue_loop(container))
