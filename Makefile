MEASUREMENT_MODE ?= all
IMAGE_VERSION ?= latest
# see Dockerfile.geth
GETH_VERSION_SHA ?= unspecified

build: build-geth build-evmone build-openethereum
	
build-geth:
	docker build -f Dockerfile.geth \
		--tag  "gas-cost-estimator/geth_${MEASUREMENT_MODE}:${IMAGE_VERSION}" \
		--build-arg  MEASUREMENT_MODE=${MEASUREMENT_MODE} \
		--build-arg  GETH_VERSION_SHA=${GETH_VERSION_SHA} \
		.

build-evmone:
	docker build -f Dockerfile.evmone \
	  --tag  "gas-cost-estimator/evmone_${MEASUREMENT_MODE}:${IMAGE_VERSION}" \
		.

build-openethereum:
	docker build -f Dockerfile.openethereum \
		--tag  "gas-cost-estimator/openethereum_${MEASUREMENT_MODE}:${IMAGE_VERSION}" \
		.

measure-geth:
	docker run --rm \
		--privileged \
		--security-opt seccomp:unconfined \
		-it gas-cost-estimator/geth_${MEASUREMENT_MODE}:${IMAGE_VERSION} \
		sh -c "cd src && python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --mode ${MEASUREMENT_MODE} --sampleSize=5 --nSamples=1"
