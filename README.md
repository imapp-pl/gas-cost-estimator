# gas-cost-estimator

[Document with the results of the `gas-cost-estimator` research project](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/gas-cost-estimator.md)

## Docker - reports

In order to build locally the docker image execute in the repository root

```shell
docker build ./src/analysis -f Dockerfile.reports -t imapp-pl/gas-cost-estimator/reports:4.0
```

Note that the context is `./src/analysis` in order to decrease the data size. 
The image includes the report notebooks -- files. 
But the bytecode programs and measurement resutls need to be provided.
For now, use `/data` volume to pass input files and retrieve an output report.

To render `measure_marginal` report provide your params and an output file and execute the command:

```shell
docker run -it -v /your/path/to/data:/data --rm imapp-pl/gas-cost-estimator/reports:4.0 Rscript -e "rmarkdown::render('/reports/measure_marginal_single.Rmd', params = list(env = 'erigon', programs='pg_marginal_full5_c50_step1_shuffle.csv', results='erigon_pg_marginal_full5_c50_step1_shuffle_size_10.csv'), output_file = '/data/erigon_measure_marginal_single.html')"
```

