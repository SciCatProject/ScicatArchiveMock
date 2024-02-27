# Scicat - Archival System Mockup
## Description
This script will simulate an archival system where everything gets indicated as `archived`/`retrieved` on demand

## Using RabbitMQ with `scicatlive`
In order to simulate a production environment better, you can start up a RabbitMQ server using the `rabbitmq/start.sh` script after you've run the `docker-compose.yaml` file of the `scicatlive` project

You must configure the `scicatlive` project to expect an MQTT server running, and to post jobs created on it to it.

The `rabbitmq` subfolder contains a complimentary dockerfile and docker-compose script to add a RabbitMQ instance to the `scicatlive` project. However, `catamel` (scicat backend) must be configured to use this RabbitMQ service.

At this point, you can use the `mqtt_job_resolver.py` script (doesn't exist yet) to automatically resolve any and all archival / retrieval job requests. It works as a background service.