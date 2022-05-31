FROM python:slim

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install python3-pip
RUN python3 -m pip install --upgrade pip

RUN apt-get -y install apt-transport-https
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev apt-utils
RUN apt-get -y install wget 
RUN apt-get -y install gpg
RUN apt-get -y install git

RUN touch /etc/apt/sources.list.d/tor.list
RUN echo "   deb     [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org bullseye main" >> /etc/apt/sources.list.d/tor.list
RUN echo "   deb-src [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org bullseye main" >> /etc/apt/sources.list.d/tor.list
RUN wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --dearmor | tee /usr/share/keyrings/tor-archive-keyring.gpg >/dev/null
RUN apt-get -y update
RUN apt-get -y install tor deb.torproject.org-keyring

WORKDIR /yatch
COPY main.py .
COPY yatch.sh .
RUN chmod +x yatch.sh

COPY templates templates
COPY requirements.txt /yatch/requirements.txt
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/torproject/stem.git


ENTRYPOINT [ "./yatch.sh" ] 
