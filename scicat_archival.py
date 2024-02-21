from typing import Union, Any
import requests
from datetime import datetime

class ArchivalMockException(Exception):
    pass

def create_job(base_url: str, token: str, retrieval: bool = False, dataset_pid: str = "", dataset_files: list[str] = [], 
               dataset_list: Union[None, list] = None) -> None:
    # NOTE: if you want to send more than one dataset per job, you must use dataset_list
    #   otherwise use dataset pid and dataset files for a "general case"
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
    params = {'access_token': token}
    r = requests.post(url=base_url+'/Jobs', params=params, json=job_json)
    if not r.status_code == 200:
        raise ArchivalMockException("{} - {}".format(r.status_code, r.reason))

def find_job(base_url: str, token: str, search_term: str) -> str:
    # TODO
    return ""

def handle_job(base_url: str, token: str, job_id: str) -> None:
    # TODO
    pass

def create_and_handle_job(base_url: str, token: str, dataset_list: list) -> None:
    create_job(base_url, token, dataset_list)
    # TODO: the following functions
    job_id = find_job(base_url, token, "")
    handle_job(base_url, token, job_id) # TODO: get job id!!!!!

def finalize_dataset():
    pass