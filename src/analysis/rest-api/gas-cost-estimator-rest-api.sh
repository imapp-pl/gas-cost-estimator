#!/bin/bash

PYTHONPATH=/rest-api uwsgi --ini /rest-api/gas-cost-estimator-rest-api.ini >uwsgi.stdout 2>uwsgi.stderr
