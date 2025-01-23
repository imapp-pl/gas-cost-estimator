#!/bin/bash
# More safety, by turning some bugs into errors.
set -o errexit -o pipefail -o noclobber -o nounset

help() {
    echo "This script generates the final report for Gas Cost Estimator with comparison to the current gas cost schedule"
    echo "Docker is required and the recent image imapp-pl/gas-cost-estimator/reports:4.0"
    echo "For more info see https://github.com/imapp-pl/gas-cost-estimator"
    echo
    echo "The script merely runs Docker container to generate the report"
    echo "Usage:"
    echo " -h, --help                  Prints this help and exit"
    echo " -w, --working-dir <folder>  The working directory that contains all input and output files"
    echo "                             The Docker volume /data is mounted at this point"
    echo "                             By default equals pwd, if set then must be an absolute path"
    echo "                             All input and output files must be relative to the working directory"
    echo " -r, --results <file>        The comma separated list of .csv files with estimated costs, originating from marginal or arguments reports"
    echo "                             Must be in the format provided by marginal or arguments reports"
    echo "                             Wildcards are supported"
    echo "                             It is required"
    echo " -g, --current-gas-cost <file>"
    echo "                             The file with the current gas cost schedule and the report settings"
    echo "                             The default file is included, can be overwritten"
    echo " -d, --details <1,t,true,on> Whether the report should include more details, detailed graphs"
    echo "                             The default is false"
    echo " -s, --output-dir <folder>   The subfolder to place output files in"
    echo "                             The default behaviour is no subfolder"
    echo "                             Note that -c and -o ignore this setting"
    echo " -c, --output-comparison <file>"
    echo "                             The output csv file with the alternative gas cost schedule and comparison"
    echo "                             The default name is final_gas_schedule_comparison.csv with regard to output-dir"
    echo " -o, --output-report <file>  The output html file with the report"
    echo "                             The default name is final_estimation.html with regard to output-dir"
    echo
    echo "Examples:"
    echo "  ./generate_final_report.sh -r estimated_cost_marginal_full_geth.csv"
    echo "    this is equivalent to (after autodetection) the following"
    echo "  ./generate_final_report.sh -r estimated_cost_marginal_full_geth.csv -c final_gas_schedule_comparison.csv -o final_estimation.html"
    echo "    this looks for input files in the current directory and saves output files in the current directory"
    echo "  ./generate_final_report.sh -r estimated_cost_marginal_full_geth.csv -w /home/user/gas-cost-reports"
    echo "  ./generate_final_report.sh -r estimated_cost_marginal_full_geth.csv -g my-current_gas_cost.csv"
    echo "  ./generate_final_report.sh -r reports-2025-01-21/estimated_cost_marginal_*,reports-2025-01-21/estimated_cost_arguments_* -s reports-2025-01-21"
    echo "    this reads input files from reports-2025-01-21 folder and saves output files to reports-2025-01-21 folder"
    echo "  ./generate_final_report.sh -r reports-2025-01-21/estimated_cost_marginal_*"
    echo "    do not use this as the wildcard expands in place, use this instead"
    echo "  ./generate_final_report.sh -r \"reports-2025-01-21/estimated_cost_marginal_*\""
}

if [ "$#" == 0 ]; then
    help
    exit 0
fi

# options
LONGOPTS=working-dir:,output-dir:,results:,current-gas-cost:,details:,output-comparison:,output-report:,help
OPTIONS=w:,s:,r:,g:,d:,c:,o:,h

# -temporarily store output to be able to check for errors
# -activate quoting/enhanced mode (e.g. by writing out “--options”)
# -pass arguments only via   -- "$@"   to separate them correctly
# -if getopt fails, it complains itself to stdout
PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@") || exit 2
# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"

WORKING_DIR=`pwd`
OUTPUT_DIR=""
RESULTS_RAW=""
while true; do
    case "$1" in
        -w|--working-dir)
            WORKING_DIR="$2"
            shift 2
            ;;
        -s|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -r|--results)
            RESULTS_RAW="$2"
            shift 2
            ;;
        -h|--help)
	    help
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            shift 2
            ;;
    esac
done

# required in any case
if [ -z "${RESULTS_RAW}" ]; then 
    echo "the input estimated cost file/files are required"
    exit 3
fi

# this is the trick to expand wildcards, into an array
RESULTS_ARR=( $(grep -Eo '[^\\s,]*[^,]*[^\\s,]*' <<<"${RESULTS_RAW}") )
# and concat an array back again
RESULTS=$(IFS=, ; echo "${RESULTS_ARR[*]}")

# add trailing / to output dir if necessary
if [ ! -z "${OUTPUT_DIR}" ]; then
    if [[ ! "${OUTPUT_DIR}" == */ ]]; then
         OUTPUT_DIR="${OUTPUT_DIR}/"
    fi
fi

if [ ! -z "${OUTPUT_DIR}" ]; then
    mkdir -p "${WORKING_DIR}/${OUTPUT_DIR}"
fi

# set default values for params
CURRENT_GAS_COST_PARAM=""
DETAILS_PARAM=""
OUTPUT_COMPARISON="${OUTPUT_DIR}final_gas_schedule_comparison.csv"
OUTPUT_REPORT="${OUTPUT_DIR}final_estimation.html"

# again
eval set -- "$PARSED"
while true; do
    case "$1" in
        -g|--current-gas-cost)
            CURRENT_GAS_COST_PARAM=", current_gas_cost='$2'"
            shift 2
            ;;
        -d|--details)
            DETAILS_PARAM=", details='$2'"
            shift 2
            ;;
        -c|--output-comparison)
            OUTPUT_COMPARISON="$2"
            shift 2
            ;;
        -o|--output-report)
            OUTPUT_REPORT="$2"
            shift 2
            ;;
         --)
            shift
            break
            ;;
        *)
            shift 2
            ;;
    esac
done

# basic validation
if [ -z "${OUTPUT_REPORT}" ]; then
    echo output-report is not set or detected
    exit 4
fi

# walkaround, docker sets new files to root:root ownership
touch "${WORKING_DIR}/${OUTPUT_COMPARISON}"
touch "${WORKING_DIR}/${OUTPUT_REPORT}"

eval "docker run -it -v ${WORKING_DIR}:/data --rm imapp-pl/gas-cost-estimator/reports:4.0 Rscript -e \"rmarkdown::render('/reports/final_estimation.Rmd', params = list(estimate_files='${RESULTS}', output_comparison_file='${OUTPUT_COMPARISON}'${DETAILS_PARAM}${CURRENT_GAS_COST_PARAM}), output_file = '/data/${OUTPUT_REPORT}')\""

