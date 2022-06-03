MEASUREMENT_MODE ?= total
IMAGE_VERSION ?= latest
EVM ?= geth

# measurement params
VOLUME_DIR ?= /home/ubuntu/pdobacz/local
PROGRAMS ?=
SAMPLESIZE ?= 1
NSAMPLES ?= 1
MEASUREMENT_SUFFIX ?=

build:
	docker build -f Dockerfile.${EVM} \
		--tag  "gas-cost-estimator/${EVM}_${MEASUREMENT_MODE}:${IMAGE_VERSION}" \
		--build-arg  MEASUREMENT_MODE=${MEASUREMENT_MODE} \
		.

measure:
	docker run --rm \
	  --privileged \
		--security-opt seccomp:unconfined \
		-v ${VOLUME_DIR}:/srv/local \
		-it gas-cost-estimator/${EVM}_${MEASUREMENT_MODE}:${IMAGE_VERSION} \
		sh -c "cd src && cat /srv/local/${PROGRAMS}.csv | python3 instrumentation_measurement/measurements.py measure --evm ${EVM} --mode ${MEASUREMENT_MODE} --sampleSize=${SAMPLESIZE} --nSamples=${NSAMPLES} > /srv/local/${EVM}_${PROGRAMS}_${SAMPLESIZE}_${NSAMPLES}${MEASUREMENT_SUFFIX}.csv"

trace:
	docker run --rm \
		-v ${VOLUME_DIR}:/srv/local \
		-it gas-cost-estimator/geth_total:${IMAGE_VERSION} \
		sh -c "cd src && cat /srv/local/${PROGRAMS}.csv | python3 instrumentation_measurement/measurements.py measure --evm geth --mode trace --sampleSize 1 > /srv/local/trace_${PROGRAMS}${MEASUREMENT_SUFFIX}.csv"
