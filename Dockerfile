FROM alpine:3

ARG USERNAME="user"
ARG GROUPNAME="job_mock"
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

ADD scicat_common.py /job_mock/scicat_common.py
ADD scicat_archival.py /job_mock/scicat_archival.py
ADD job_handler_mq_client_mock.py /job_mock/run.py

RUN apk add python3 py3-pip curl && \
  python -m venv /job_mock/venv && \
  . /job_mock/venv/bin/activate && \
  pip install pika pyscicat && \
  addgroup --gid "${USER_GID}" "${GROUPNAME}" && \
  adduser -u ${USER_UID} -S ${USERNAME} -G ${GROUPNAME} && \
  chown -R ${USER_UID} /job_mock && \
  chmod 770 /job_mock && \
  chmod 550 /job_mock/scicat_common.py /job_mock/scicat_archival.py /job_mock/run.py /job_mock/venv

USER ${USERNAME}
WORKDIR /job_mock
ENV PATH="/job_mock/venv/bin:$PATH"
CMD python -u run.py --scicat-url "${SCICAT_URL}" --rabbitmq-url "${RABBITMQ_URL}" -u "${USERNAME}" -p "${PASSWORD}" -t "${TOKEN}"