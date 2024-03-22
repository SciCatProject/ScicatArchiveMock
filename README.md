# Scicat - Archival System Mockup

This set of scripts will simulate an archival system where datasets get `archived`/`retrieved` on demand

## Archive Mock Service

### Description

It listens to jobs posted to rabbitmq by the Backend. This will instruct the Archive Mock to run the script that simulates the archive system, for both archival and retrieval. After retrieving a job from `RabbitMQ`, the job is executed. An archival job is executed as such:

1. Mark job as being handled (jobStatusMessage: `"inProgress"`)
2. Mark dataset(s) as being archived (archivable: `false`, archiveStatusMessage: `"started"`)
3. Add `DataBlocks`
4. Mark dataset(s) as archived (retrievable: `true`, archiveStatusMessage: `"datasetOnArchiveDisk"`)
5. Mark job as done (jobStatusMessage: `"finishedSuccessful"`)

Note: the way the DataBlocks (*not* OrigDatablocks) are generated in the mock does not necessarily correspond to any specific implementation of the archival system, it's just an example.

A similar script handles retrieval:

1. Mark job as being handled. (jobStatusMessage: `"inProgress"`)
2. Mark dataset(s) as being retrieved (retrieve status message: `"started"`)
3. Mark dataset(s) as retrieved (retrieve status message: `"datasetReceived"`)
4. Mark job as done (jobStatusMessage: `"finishedSuccessful"`)

### Running locally

It requires having access to a RabbitMQ and a Scicat Backend instance, with the latter configured to post jobs to the former. It depends on `pika` for RabbitMQ communication. 

`python3 job_handler_mq_client_mock.py [PARAMS]`

After starting the script, it will wait for any archival/retrieval jobs posted to RabbitMQ, and will attempt to handle them. It's possible for datasets to get stuck in a non-archivable and non-retrievable state, if the Job or Dataset has any unexpected (as in, out-of-spec) elements.

List of parameters:
| Parameter           | Description                                             | Required                         |
| ------------------- | ------------------------------------------------------- | -------------------------------- |
| --scicat-url        | The base url of the backend (usually ends in `/api/v_`) | Yes                              |
| --scicat-user       | The user to use for connecting to scicat                | No (can use token instead)       |
| --scicat-password   | The user's password for connecting to scicat            | No (can use token instead)       |
| --scicat-token      | The token to use for connecting to scicat               | No (can use user and pw instead) |
| --rabbitmq-url      | RabbitMQ API url                                        | Yes                              |
| --rabbitmq-user     | the username used for accessing RabbitMQ                | Yes                              |
| --rabbitmq-password | the password used for accesing RabbitMQ                 | Yes                              |

### Docker Container

It still requires some kind of access to a SciCat Backend and a RabbitMQ instance. You can use [scicatlive](https://github.com/SciCatProject/scicatlive) if you don't have any instance of those two to test with.

| Variable | Corresponding Parameter |
| -------- | ----------------------- |
| SCI_URL  | `--scicat-url`          |
| SCI_USER | `--scicat-user`         |
| SCI_PW   | `--scicat-password`     |
| TOKEN    | `--scicat-token`        |
| RMQ_URL  | `--rabbitmq-url`        |
| RMQ_USER | `--rabbitmq-user`       |
| RMQ_PW   | `--rabbitmq-password`   |

### Utility Scripts

1. Use `python scicat_ingestion.py  -b "http://catamel.localhost/api/v3/" -u admin -p 2jf70TPNZsS --path [PATH TO DATASET]` to ingest a dataset. NOTE: You must add a `transfer.yaml` file (example is included in this repository) to the dataset which will serve as a metadata source for the ingestor.
2. Use `python job_create.py -b "http://catamel.localhost/api/v3/" -u admin -p 2jf70TPNZsS --dataset-id [PID of the previously created dataset] --job-type [archival / retrieval]` to create an archival / retrieval job (new datasets can only be archived initially, and archival can only happen once)
3. The job will almost immediately be handled by the archival mock script
4. You can check the `datasetlifecycle` of your dataset to see that it has been archived / retrieved using the backend's [swagger ui](http://catamel.localhost/explorer) with the `GET /Datasets/{id}` endpoint

## Basic Auto-Ingester and Archival for API checking
You can use the `dataset_ingest_job_mock.py` script to ingest and archive datasets by providing it a source folder of datasets (with each dataset having its own subfolder), and each dataset must have a transfer.yaml as a source of metadata (example provided with this repository). This is mostly useful as an API test, it doesn't replicate the job message queue, but it also alleviates the dependency on RabbitMQ (scicat is obviously still needed). The command to use it is the following: 

`python dataset_ingest_job_mock.py -b [backend address] -u [username] -p [password] --path [path to dataset collection]`

Optionally, one can add `--check-dataset-duplication` to avoid ingesting the same datasets multiple times
