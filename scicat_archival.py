from typing import Union, Any
from scicat_common import check_request_response
import requests
from datetime import datetime
import urllib.parse

class ArchivalMockException(Exception):
    pass

# simulates dataIngestion for creating the job
def create_job(base_url: str, token: str, retrieval: bool = False, dataset_pid: str = "", 
               dataset_files: list[str] = [], dataset_list: Union[None, list] = None) -> None:
    # NOTE: if you want to send more than one dataset per job, you must use dataset_list
    #   otherwise use dataset pid and dataset files for a "general case"
    # NOTE: when creating an archival job, the datasetLifecycle is automatically updated by
    #   scicat to mark it as non-archivable!
    if dataset_list is None:
        job_json = {
            "type": "retrieve" if retrieval else "archive",
            "datasetList": [
                {
                    "pid": dataset_pid,
                    "files": [dataset_files]
                }
            ]
        }
    else:
        job_json = {
            "type": "retrieve" if retrieval else "archive",
            "datasetList": dataset_list,
        }
    access_token = {'access_token': token}
    r = requests.post(url=base_url+'/Jobs', params=access_token, json=job_json)
    check_request_response(r, "can't create job")
    return r.json().get('id')

# simulates node-red for forwarding jobs
def forward_job(base_url: str, token: str, job_id: str) -> list[dict]:
    access_token = {'access_token': token}
    r = requests.get(url=base_url+'/Jobs/datasetDetails', params={'jobId': job_id} | access_token)
    check_request_response(r, "can't get job's dataset details")
    dataset_list = r.json()
    if not isinstance(dataset_list, list) or dataset_list == []:
        raise ArchivalMockException("unexpected response or empty list: {}".format(dataset_list))
    r = requests.put(url=base_url+'/Jobs/'+urllib.parse.quote(job_id, safe=''), 
                     json={"jobStatusMessage": "jobForwarded"}, params=access_token)
    check_request_response(r, "can't mark job as forwarded")
    return dataset_list

def check_dataset(dataset: dict, archivable: bool = False, retrievable: bool = False):
    if not isinstance(dataset, dict):
        raise ArchivalMockException("dataset is invalid: {}".format(dataset))
    dataset_lifecycle = dataset.get('datasetlifecycle')
    dataset_id = dataset.get('pid')
    if dataset_id is None or not isinstance(dataset_lifecycle, dict):
        raise ArchivalMockException("dataset is invalid: {}".format(dataset))
    if not ((archivable == dataset_lifecycle.get('archivable')) or \
           (retrievable == dataset_lifecycle.get('retrievable'))):
        raise ArchivalMockException("dataset is incompatible with desired operation: {}".format(dataset))

# simulates AREMA for archival registering
def handle_archive_job(base_url: str, token: str, job_id: str, datasets: list) -> None:
    access_token = {'access_token': token}
    for dataset in datasets:
        check_dataset(dataset) # dataset integrity check
        dataset_id = dataset.get('pid')

        # 1 - mark datasets as being archived
        r = requests.put(url=base_url+'/Datasets/'+urllib.parse.quote(dataset_id, safe=''), 
                         params=access_token, json={"datasetlifecycle": {"archiveStatusMessage": "started"}})
        check_request_response(r, "can't mark dataset as being archived")

        # 2 - send datablocks
        r = requests.get(url=base_url+'/Datasets/'+urllib.parse.quote(dataset_id, safe=''), 
                         params=access_token | {"filter": '{"include": [{"relation": "origdatablocks"}]}'})
        check_request_response(r, "can't get origdatablocks of dataset")
        orig_datablocks = r.json().get('origdatablocks')
        if not isinstance(orig_datablocks, list): 
            ArchivalMockException("invalid orig datablocks for dataset: {}".format(dataset_id))
        for orig_datablock in orig_datablocks:
            # create datablock by adapting orig datablock (it's a mock after all)
            datablock = dict(orig_datablock)
            datablock.pop('createdBy', None)
            datablock.pop('updatedBy', None)
            datablock.pop('createdAt', None)
            datablock.pop('updatedAt', None)
            od_id = datablock.pop('id', None)
            if od_id is None:
                ArchivalMockException("OrigDatablock doesn't have id for dataset {}".format(dataset_id))
            datablock['archiveId'] = '/archive/{}.tar'.format(od_id)
            datablock['packedSize'] = datablock.get('size')
            datablock['chkAlg'] = 'sha1'
            datablock['version'] = '2.0.2'
            # send datablock
            r = requests.post(url=base_url+'/Datablocks', params=access_token, json=datablock)
            check_request_response(r, "can't create datablock for orig datablock {} in dataset {}".format(od_id, 
                                                                                                          dataset_id
                                                                                                          ))
        
        # 3 - mark datasets as archived
        r = requests.put(url=base_url+'/Datasets/'+urllib.parse.quote(dataset_id, safe=''), 
                 params=access_token, json={"datasetlifecycle": {"retrievable": True, 
                                                                 "archiveStatusMessage": "datasetOnArchiveDisk"}})
        check_request_response(r, "can't mark dataset as archived")

    # mark job as successfully finished
    r = requests.put(url=base_url+'/Jobs/'+urllib.parse.quote(job_id, safe=''), 
                     json={"jobStatusMessage": "finishedSuccessful"}, 
                     params=access_token)
    check_request_response(r, "can't mark job as finished")
    return

def handle_retrieve_job(base_url: str, token: str, job_id: str, datasets: list) -> None:
    for dataset in datasets:
        check_dataset(dataset, retrievable=True) # dataset integrity check
        dataset_id = dataset.get('pid')
        access_token = {'access_token': token}

        # mark dataset as being retrieved
        r = requests.put(url=base_url+'/Datasets/'+urllib.parse.quote(dataset_id, safe=''), 
                     params=access_token, json={"datasetlifecycle": {"retrieveStatusMessage": "started"}})
        check_request_response(r, "can't mark dataset as being retrieved")

        # mark dataset as retrieved
        r = requests.put(url=base_url+'/Datasets/'+urllib.parse.quote(dataset_id, safe=''), 
                     params=access_token, json={"datasetlifecycle": {"retrieveStatusMessage": "datasetRetrieved"}})
        check_request_response(r, "can't mark dataset as retrieved")


    # mark job as successfully finished
    r = requests.put(url=base_url+'/Jobs/'+urllib.parse.quote(job_id, safe=''), 
                     json={"jobStatusMessage": "finishedSuccessful"}, 
                     params=access_token)
    check_request_response(r, "can't mark job as finished")
    pass