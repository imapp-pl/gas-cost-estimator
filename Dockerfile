FROM python:3.8


WORKDIR /srv/app/

# base for python
COPY ./src/program_generator/requirements.txt /srv/app/src/program_generator/requirements.txt
RUN pip install -r src/program_generator/requirements.txt

# base for golang
ADD https://golang.org/dl/go1.17.1.linux-amd64.tar.gz .
RUN tar -C /usr/local -xzf ./go1.17.1.linux-amd64.tar.gz
RUN rm go1.17.1.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin
ENV GOPATH=/srv/app/.go
ENV GO111MODULE=off
ENV GOBIN=/srv/app/.go/bin

# fixed golang dependencies
RUN go get github.com/ethereum/go-ethereum

# get our files
WORKDIR /srv/app/.go/src/github.com/ethereum/go-ethereum
RUN git remote add imapp-pl https://github.com/imapp-pl/go-ethereum.git
RUN git fetch imapp-pl wallclock
RUN git checkout wallclock
COPY ./src/ /srv/app/src/

WORKDIR /srv/app/src/instrumentation_measurement
RUN go get ./geth/...

WORKDIR /srv/app/

# check correct host configuration
RUN chmod a+x ./src/check_clocksource.sh
RUN ./src/check_clocksource.sh

# our runtime config
ENV GOGC=off
