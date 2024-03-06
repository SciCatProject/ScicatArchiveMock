import pika, sys, os
import json
from scicat_common import scicat_username_login
from scicat_archival import forward_job, handle_archive_job, handle_retrieve_job, ArchivalMockException

class JobHandlerException(Exception):
    pass

def main(scicat_url: str, rabbitmq_url: str, token: str):
    def job_callback(ch, method, properties, body: bytes):
        print("Job received... ", end='')
        job = json.loads(body)
        job_id = job.get('id')
        job_type = job.get('type')
        
        if job_id is None:
            print("ERR: No job id was given (skipped). Received: {}".format(job))
            return
        print("handling {}... ".format(job_id), end='')
        try:
            dataset_list =                       forward_job(scicat_url, token, job_id)
            if   job_type ==  'archive':  handle_archive_job(scicat_url, token, job_id, dataset_list)
            elif job_type == 'retrieve': handle_retrieve_job(scicat_url, token, job_id, dataset_list)
            else: 
                print("ERR: Invalid job type provided (skipped). Received: {}".format(job))
                return
        except ArchivalMockException as e:
            print("ERR: Archival failed for {} (skipped): {}".format(job_id, e))
            return
        print("DONE.")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_url))
    channel = connection.channel()
    channel.queue_declare(queue='client.jobs.write', durable=True)
    channel.basic_consume(queue='client.jobs.write', on_message_callback=job_callback, auto_ack=True)

    print(' [*] Waiting for jobs. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    # argument parsing
    import argparse
    parser = argparse.ArgumentParser(
        prog="Scicat Job Handler Mock",
        description="This application acts as a RabbitMQ client to mock the handling of archival/retrieval jobs",
        epilog="Refer to README.md to learn more"
    )
    parser.add_argument("--scicat-url", required=True)
    parser.add_argument("--rabbitmq-url", required=True)
    parser.add_argument("-u", "--user")
    parser.add_argument("-p", "--password")
    parser.add_argument("-t", "--token")
    args = parser.parse_args()

    scicat_url = args.scicat_url
    rabbitmq_url = args.rabbitmq_url
    user = args.user
    password = args.password
    token = args.token

    if token is None:
        token = scicat_username_login(scicat_url, user, password)

    try:
        main(scicat_url, rabbitmq_url, token)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)