# Instructions for installing RabbitMQ

On linux, to install rabbitMQ, use the bash script "install_rabbitMQ.sh" with command below (tested on Ubuntu 22.04). This installs Erlang, as a dependancy, and rabbitMQ.

`sudo ./install_rabbitMQ.sh`


To start a rabbitMQ cluster, run the following command:

`sudo rabbitmq-server`

and to stop it:

`sudo rabbitmqctl stop`