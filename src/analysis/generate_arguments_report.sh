#!/bin/bash
# More safety, by turning some bugs into errors.
set -o errexit -o pipefail -o noclobber -o nounset

help() {
    echo "This script generates the arguments report for Gas Cost Estimator"
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
    echo " -r, --results <file>        The .csv file with measurements results"
    echo "                             Must be in the format program_id,sample_id,total_time_ns may contain other data"
    echo "                             If the file name is of the form results_arguments_<MEASUREMENT_GROUP>_<EVM>.csv, the script autodetects other param files"
    echo "                             It is required"
    echo " -e, --evm <name>            The name of EVM client. If not autodetected, it is required"
    echo " -p, --programs <file>       The csv file with programs used for measurements"
    echo "                             If not autodetected, it is required"
    echo " -m, --marginal-estimated-cost <files>"
    echo "                             A comma separated list of csv files. These are output of the marginal report generation."
    echo "                             The marginal estimated cost of opcodes is for comparison in the report"
    echo "                             It is optional"
    echo " -d, --details <1,t,true,on> Whether the report should include more details, detailed graphs"
    echo "                             The default is true"
    echo " -s, --output-dir <folder>   The subfolder to place output files in"
    echo "                             The default behaviour is no subfolder"
    echo "                             Note that -c and -o ignore this setting"
    echo " -c, --output-estimated-cost <file>"
    echo "                             The output csv file with the estimated costs of arguments"
    echo "                             If not autodetected, it is required"
    echo " -o, --output-report <file>  The output html file with the report"
    echo "                             If not autodetected, it is required"
    echo " -q, --quiet                 Suppress the output"
    echo
    echo "Examples:"
    echo "  ./generate_arguments_report.sh -r results_arguments_arithmetic_geth.csv"
    echo "    this is equivalent to (after autodetection) the following"
    echo "  ./generate_arguments_report.sh -r results_arguments_arithmetic_geth.csv -e geth -p pg_arguments_arithmetic.csv -c estimated_cost_arguments_arithmetic_geth.csv -o report_arguments_arithmetic_geth.html"
    echo "    this looks for input files in the current directory and saves output files in the current directory"
    echo "  ./generate_arguments_report.sh -r results_arguments_arithmetic_geth.csv -s reports-2025-01-21"
    echo "  ./generate_arguments_report.sh -r results_arguments_arithmetic_geth.csv -q"
    echo "  ./generate_arguments_report.sh -r my_dir/results_arguments_arithmetic_geth.csv -s reports-2025-01-21"
    echo "    this reads input files from my_dir folder and saves output files to my_dir/reports-2025-01-21 folder"
    echo "  ./generate_arguments_report.sh -r results_arguments_arithmetic_geth.csv -w /home/user/gas-cost-reports"
}

if [ "$#" == 0 ]; then
    help
    exit 0
fi

# options
LONGOPTS=working-dir:,output-dir:,evm:,programs:,results:,marginal-estimated-cost:,details:,output-estimated-cost:,output-report:,help,quiet
OPTIONS=w:,s:,e:,p:,r:,m:,d:,c:,o:,h,q

# -temporarily store output to be able to check for errors
# -activate quoting/enhanced mode (e.g. by writing out “--options”)
# -pass arguments only via   -- "$@"   to separate them correctly
# -if getopt fails, it complains itself to stdout
PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@") || exit 2
# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"

WORKING_DIR=`pwd`
OUTPUT_DIR=""
RESULTS=""
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
            RESULTS="$2"
            shift 2
            ;;
        -h|--help)
	    help
            exit 0
            ;;
        -e|--evm|-p|--programs|-m|--marginal-estimated-cost|-d|--details|-c|--output-estimated-cost|-o|--output-report) # just validation
            shift 2
            ;;
        -q|--quiet) # just validation
            shift 
            ;;
        --)
            shift
            break
            ;;
        *)
            echo Unrecognized argument "$1"
            exit 2            
            ;;
    esac
done

# required in any case
if [ -z "${RESULTS}" ]; then 
    echo "the measurement result file is required"
    exit 3
fi

# add trailing / to output dir if necessary
if [ ! -z "${OUTPUT_DIR}" ]; then
    if [[ ! "${OUTPUT_DIR}" == */ ]]; then
         OUTPUT_DIR="${OUTPUT_DIR}/"
    fi
fi

# set default values for params if RESULTS is parsable
EVM=""
PROGRAMS=""
MARGINAL_ESTIMATED_COST_PARAM=""
DETAILS_PARAM=""
OUTPUT_ESTIMATED_COST=""
OUTPUT_REPORT=""
QUIET_PARAM=""
PATTERN="(.*)results_arguments_(\w+)_([a-zA-Z0-9]+)\.csv$"
if [[ ${RESULTS} =~ ${PATTERN} ]]; then
    CTX="${BASH_REMATCH[1]}"
    MEASUREMENT_GROUP="${BASH_REMATCH[2]}"
    EVM="${BASH_REMATCH[3]}"
    PROGRAMS="${CTX}pg_arguments_${MEASUREMENT_GROUP}.csv"
    OUTPUT_ESTIMATED_COST="${CTX}${OUTPUT_DIR}estimated_cost_arguments_${MEASUREMENT_GROUP}_${EVM}.csv"
    OUTPUT_REPORT="${CTX}${OUTPUT_DIR}report_arguments_${MEASUREMENT_GROUP}_${EVM}.html"
    if [ ! -z "${OUTPUT_DIR}" ]; then
	mkdir -p "${WORKING_DIR}/${CTX}${OUTPUT_DIR}"
    fi
else
    if [ ! -z "${OUTPUT_DIR}" ]; then
        mkdir -p "${WORKING_DIR}/${OUTPUT_DIR}"
    fi
fi

# again
eval set -- "$PARSED"
while true; do
    case "$1" in
        -e|--evm)
            EVM="$2"
            shift 2
            ;;
        -p|--programs)
            PROGRAMS="$2"
            shift 2
            ;;
        -m|--marginal-estimated-cost)
            MARGINAL_ESTIMATED_COST_PARAM=", marginal_estimated_cost='$2'"
            shift 2
            ;;
        -d|--details)
            DETAILS_PARAM=", details='$2'"
            shift 2
            ;;
        -c|--output-estimated-cost)
            OUTPUT_ESTIMATED_COST="$2"
            shift 2
            ;;
        -o|--output-report)
            OUTPUT_REPORT="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET_PARAM=", quiet=TRUE"
            shift
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
if [ -z "${EVM}" ]; then
    echo evm is not set or detected
    exit 4
fi
if [ -z "${PROGRAMS}" ]; then
    echo programs is not set or detected
    exit 4
fi
if [ -z "${OUTPUT_ESTIMATED_COST}" ]; then
    echo output-estimated-cost is not set or detected
    exit 4
fi
if [ -z "${OUTPUT_REPORT}" ]; then
    echo output-report is not set or detected
    exit 4
fi

# walkaround, docker sets new files to root:root ownership
touch "${WORKING_DIR}/${OUTPUT_ESTIMATED_COST}"
touch "${WORKING_DIR}/${OUTPUT_REPORT}"

eval "docker run -it -v ${WORKING_DIR}:/data --rm imapp-pl/gas-cost-estimator/reports:4.1 Rscript -e \"rmarkdown::render('/reports/measure_arguments_single.Rmd', params = list(env = '${EVM}', programs='${PROGRAMS}', results='${RESULTS}', output_estimated_cost='${OUTPUT_ESTIMATED_COST}'${DETAILS_PARAM}${MARGINAL_ESTIMATED_COST_PARAM}), output_file = '/data/${OUTPUT_REPORT}'${QUIET_PARAM})\""

