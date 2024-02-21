from pyscicat.client import ScicatClient, encode_thumbnail, ScicatLoginError, ScicatCommError
from pyscicat.model import Attachment, Datablock, OrigDatablock, CreateDatasetOrigDatablockDto, DataFile, Dataset, \
    RawDataset, Ownable
from pathlib import Path
from typing import Union
from datetime import datetime
import os
import requests

class IngestionException(Exception):
    pass

def dataset_check(base_url: str, token: str, file_path: Path):
    scicat = ScicatClient(base_url=base_url, token=token)

    result = scicat.find_datasets({"sourceFolder": str(file_path)})
    if len(result) > 0: raise IngestionException("already exists")
    return (True, "")

def create_dataset(path: Path, base_url: str, token: str, transfer_config: dict[str: any] = [], 
                   file_paths: list[str] = []) -> tuple[str, list[str]]:
    # Create a client object. The account used should have the ingestor role in SciCat
    scicat = ScicatClient(base_url=base_url, token=token)


    # Create a RawDataset object with settings for your choosing. Notice how
    # we pass the `ownable` instance.
    fileCount = len(file_paths)
    if fileCount == 0:
        raise IngestionException("no files contained in dataset")

    rel_paths = [os.path.relpath(p, path) for p in file_paths]
    file_sizes = [os.path.getsize(p) for p in file_paths]
    file_times = [os.path.getmtime(p) for p in file_paths]
    datasetTime = datetime.fromtimestamp(max(file_times)).isoformat()

    # Create an Ownable that will get reused for several other Model objects
    ownable = Ownable(
        ownerGroup="mars", # only obligatory part
        accessGroups=transfer_config.get('accessGroups'), 
        instrumentGroup=transfer_config.get('othergroup')
    )

    ownerOrcids = ';'.join(['' if i.get('orcid') is None else i.get('orcid') for i in transfer_config['owners']])
    ownerNames = ';'.join(['' if i.get('name') is None else i.get('name') for i in transfer_config['owners']])
    ownerEmails = ';'.join(['' if i.get('email') is None else i.get('email') for i in transfer_config['owners']])
    principalInvestigators = ';'.join(transfer_config.get('principalInvestigators'))

    dataset = RawDataset(
        contactEmail=transfer_config.get('contactEmail'),
        creationTime=datasetTime,
        datasetName=transfer_config.get('datasetName'),
        description=transfer_config.get('description'),
        instrumentId=transfer_config.get('instrumentId'),
        isPublished=transfer_config.get('isPublished'),
        keywords=transfer_config.get('keywords'),
        license=transfer_config.get('license'),
        numberOfFiles = fileCount,
        orcidOfOwner=ownerOrcids if not ownerOrcids == '' else None,
        owner=ownerNames,
        ownerEmail=ownerEmails if not ownerEmails == '' else None,
        size=sum(file_sizes), # optional
        sourceFolder=str(path.resolve()), # this will have to reflect the retrieval location for the archival system 
        #sourceFolderHost="earth.net", # same as above but the network host part (instead of filesystem)
        validationStatus=transfer_config.get('validationStatus'),
        version="4.0.0", # optional
        scientificMetadata={}, # optional, this will be determined later
        principalInvestigator=principalInvestigators if not principalInvestigators == '' else None,
        creationLocation=transfer_config.get('creationLocation'),
        #dataFormat="someformat", # optional, this should be autodetected eventually
        sampleId=transfer_config.get('sampleId'),
        **ownable.model_dump()
    )
    r = requests.post(base_url + '/Datasets/isValid', json=dataset.model_dump())
    if r.json().get('valid') == False:
        raise IngestionException("the dataset generated is invalid")
    try:
        dataset_id = scicat.datasets_create(dataset)
    except ScicatCommError as e:
        raise IngestionException("Communication with SciCat failed, cannot complete dataset job at {} due to the \
                                 following error: {}".format(path, e.message))

    # Create Datablock with DataFiles
    dataFileList = [
        DataFile(path=p, size=s, time=datetime.fromtimestamp(t).isoformat()) for (p, s, t) in zip(rel_paths, 
                                                                                                  file_sizes, 
                                                                                                  file_times)
    ]
    data_block = CreateDatasetOrigDatablockDto(
        size=42, version=1, dataFileList=dataFileList
    )
    try:
        scicat.datasets_origdatablock_create(dataset_id, data_block)
    except ScicatCommError as e:
        e = "Communication with SciCat failed, cannot complete dataset job at {} \
              due to the following error: {}.".format(path, e.message)
        try: 
            scicat.datasets_delete(dataset_id)
        except ScicatCommError as e:
            e + " Additionally, cannot delete incomplete dataset, manual cleanup of \"{}\" is necessary. \
                The following comm. error was received: {}.".format(dataset_id, e.message)
        raise IngestionException(e)

    # Create Attachments
    attachments = transfer_config.get('attachments')
    for attachment in attachments:
        attach_path = attachment.get('path')
        if attach_path is None: continue
        imgType = attachment.get('type')
        if imgType is None: imgType = 'jpg'
        thumb_path = path / attach_path

        attachment = Attachment(
            datasetId=dataset_id,
            thumbnail=encode_thumbnail(thumb_path, imgType),
            caption=attachment.get('caption'),
            **ownable.model_dump(),
        )
        try:
            scicat.datasets_attachment_create(attachment)
        except ScicatCommError as e:
            # attachments are not essential
            pass
    return (dataset_id, rel_paths)
