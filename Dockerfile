FROM python:3.6.12-slim-buster
FROM ubuntu

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN 	apt-get -y update && \
	apt-get -y upgrade && \
	apt-get -y install python3 &&\
	apt-get -y install python3-pip &&\
	apt-get -y install gcc &&\
	apt-get -y install mono-mcs && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /nsfw-gang/fol
ADD . /nsfw-gang/fol

RUN pip3 install -r requirements.txt
RUN pip3 install depccg
RUN pip3 install allennlp
RUN python3 -m depccg en download
RUN python3 -m spacy download en
COPY FOL_PARSER.py /nsfw-gang/fol
CMD ["python3","FOL_PARSER.py", "-OPTIONAL_FLAG"]