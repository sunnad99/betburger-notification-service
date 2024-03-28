import celery
from utils import send_message
from credentials import TELEGRAM_TOKEN

# from celery import Celery

app = celery.Celery(
    "messages", broker="pyamqp://guest:guest@localhost/", backend="rpc://"
)


@app.task(
    acks_late=True,
    rate_limit="20/m",
    bind=True,
    auto_retry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def send_message_to_channel(self, message, chat_id):

    return send_message(
        token=TELEGRAM_TOKEN,
        chat_id=chat_id,
        message=message,
    )


# active_workers = app.control.inspect().active()
# if active_workers:
#     print(active_workers)
#     print(len(active_workers))

#     # app.control.shutdown()
# else:
#     print("No active workers yet")


# if __name__ == "__main__":
