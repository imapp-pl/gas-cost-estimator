FROM python:3.8


WORKDIR /srv/app/

COPY ./src/ /srv/app/src/
RUN pip install -r src/program_generator/requirements.txt

ADD https://golang.org/dl/go1.17.1.linux-amd64.tar.gz .
RUN tar -C /usr/local -xzf ./go1.17.1.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin
ENV GOPATH=/srv/app/.go
ENV GOGC=off
ENV GO111MODULE=off
ENV GOBIN=/srv/app/.go/bin

RUN go get github.com/ethereum/go-ethereum
WORKDIR /srv/app/.go/src/github.com/ethereum/go-ethereum
RUN git remote add imapp-pl https://github.com/imapp-pl/go-ethereum.git
RUN git fetch imapp-pl wallclock
RUN git checkout wallclock

WORKDIR /srv/app/src/instrumentation_measurement
RUN go get ./geth/...

WORKDIR /srv/app/

RUN chmod a+x ./src/check_clocksource.sh
RUN ./src/check_clocksource.sh
