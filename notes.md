# Notes about celery


To see actively running instances, use the following command in python

`app.control.inspect.active()`

Returns None when no worker is running.

to stop celery workers from running, run the following bash terminal cmd

`celery control shutdown`

or the python command

`app.control.shutdown()`

