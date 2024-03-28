import os
import subprocess
import time
from messages import app

NUM_WORKERS = 2

APP_NAME = "messages"

BASE_MULTIPLE_WORKER_CMD = f"celery -A {APP_NAME} multi start"
for i in range(NUM_WORKERS):

    worker_name = f"worker{i+1}@localhost"
    queue_name = f"queue{i+1}"
    # data = app.Worker(hostname = worker_name, detach = True, queues = [queue_name])

    # app.worker_main(argv=['worker', '--loglevel=INFO', f'--hostname={worker_name}', '--detach',f'-Q {queue_name}'])
    # print("Started worker {worker_name}".format(worker_name = worker_name))

    # Adding the worker to the command
    BASE_MULTIPLE_WORKER_CMD += f" {worker_name} -Q:{i+1} {queue_name}"

BASE_MULTIPLE_WORKER_CMD += (
    " -l INFO --pidfile=./pidfiles/%n.pid --logfile=./logs/%n%I.log"
)

print(BASE_MULTIPLE_WORKER_CMD)


output = subprocess.run(
    BASE_MULTIPLE_WORKER_CMD, shell=True, capture_output=True, text=True
)

# Wait for the workers to start
time.sleep(5)

active_workers = app.control.inspect().active()


if active_workers:

    print(active_workers)
    print(len(active_workers))

    # actual_workers = app.control.inspect().ping()
    # TODO: Check the length of the active workers against the how many actual workers are in the database
    actual_workers = NUM_WORKERS + 2
    workers_to_be_active = [f"worker{i+1}@localhost" for i in range(actual_workers)]

    if len(active_workers) == actual_workers:
        print("All workers are active")
    else:
        missing_workers = list(set(workers_to_be_active) - set(active_workers))

        print(
            "The following workers are missing and will be started now:",
            missing_workers,
        )
        # TODO: The queue names will be obtained from the database instead of hard coded here
        for worker in missing_workers:

            index = worker.split("@")[0][-1]
            queue_name = f"queue{index}"
            command = f"celery -A {APP_NAME} worker --hostname={worker} -Q {queue_name} --detach -l INFO --pidfile=./pidfiles/%n.pid --logfile=./logs/%n%I.log"
            os.system(
                command
            )  # TODO: This will have to be run using asyncio to run multiple I/O bound tasks concurrently

        # output = subprocess.run(command, shell=True)
        # print(output)
        time.sleep(5)  # Wait for the missing workers to start

    # app.control.shutdown()  # TODO: Remove after done testing
else:
    print("No active workers yet")
