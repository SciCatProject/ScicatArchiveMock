# Scicat - Archival System Mockup
## Description
This set of scripts will simulate an archival system where datasets get `archived`/`retrieved` on demand

## Basic auto-ingestion and archival for API checking
You can use the `dataset_ingest_job_mock.py` script to ingest and archive datasets by providing it a source folder of datasets (with each dataset having its own subfolder), and each dataset must have a transfer.yaml as a source of metadata (example provided with this repository). This is mostly useful as an API test, it doesn't replicate the job message queue. The command to use it is the following: 

`python3 dataset_ingest_job_mock.py -b [backend address] -u [username] -p [password] --path [path to dataset collection]`

Optionally, one can add `--check-dataset-duplication` to avoid ingesting the same datasets multiple times

## Using RabbitMQ with the official `scicatlive` repository
In order to simulate a production environment better, you can start up a RabbitMQ server using the contents of the `rabbitmq` subfolder

1. Apply the `scicat.patch` to the `931248f2cf68f7ae985c7af5a4c98573a8e189cf` commit on `master` of [scicatlive](https://github.com/SciCatProject/scicatlive/tree/931248f2cf68f7ae985c7af5a4c98573a8e189cf)
2. Start the rabbitmq server with `start.sh` in the `rabbitmq` subfolder
3. Start the docker-compose file of the modified scicatlive (`docker-compose up -d` in scicatlive)
4. `python job_handler_mq_client_mock.py -b "http://catamel.localhost/api/v3/" -u admin -p 2jf70TPNZsS` to start the archival mock

Note: if you're using a mac, add `127.0.0.1	catamel.localhost` to your `hosts` file (`/private/etc/hosts`)

Alternatively, use the [preconfigured scicatlive fork](https://github.com/consolethinks/scicatlive/tree/job_mock)

## Using the utility scripts

1. Use `python scicat_ingestion.py  -b "http://catamel.localhost/api/v3/" -u admin -p 2jf70TPNZsS --path [PATH TO DATASET]` to ingest a dataset. NOTE: You must add a `transfer.yaml` file (example is included in this repository) to the dataset which will serve as a metadata source for the ingestor.
2. Use `python job_create.py -b "http://catamel.localhost/api/v3/" -u admin -p 2jf70TPNZsS --dataset-id [PID of the previously created dataset] --job-type [archival / retrieval]` to create an archival / retrieval job (new datasets can only be archived initially, and archival can only happen once)
3. The job will almost immediately be handled by the archival mock script
4. You can check the `datasetlifecycle` of your dataset to see that it has been archived / retrieved using the backend's [swagger ui](http://catamel.localhost/explorer) with the `GET /Datasets/{id}` endpoint
