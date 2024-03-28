# Instructions for installing RabbitMQ

On linux, to install rabbitMQ, use the bash script "install_rabbitMQ.sh" with command below (tested on Ubuntu 22.04). This installs Erlang, as a dependancy, and rabbitMQ.

`sudo ./install_rabbitMQ.sh`


To start a rabbitMQ cluster, run the following command:

`sudo rabbitmq-server`

and to stop it:

`sudo rabbitmqctl stop`

To be able to see frontend dashboard for rabbitMQ in the browser, enable the management plugin by:

`sudo rabbitmq-plugins enable rabbitmq_management`

The default username and password are "guest" and "guest" respectively.

To start multiple workers:

`celery -A tasks multi start 10 -l INFO -Q:1-3 images,video -Q:4,5 data -Q default -L:4,5 DEBUG --pidfile=./pidfiles/%n.pid --logfile=./logs/%n%I.log`