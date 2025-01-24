# running quick test for all clients
echo EvmOne:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm evmone --sample_size 2

echo 
echo Geth:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm geth --sample_size 2

echo
echo Nethermind:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm nethermind --sample_size 2

echo
echo EthereumJS:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm ethereumjs --sample_size 2

echo
echo Erigon:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm erigon --sample_size 2

echo
echo Besu:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm besu --sample_size 2

echo
echo Revm:
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file gas-cost-estimator/src/stage4/pg_test.csv --evm revm --sample_size 2

