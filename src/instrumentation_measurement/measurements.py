import csv
import fire
import json
import os
import os.path
import re
import shutil
import sys
import subprocess
from io import StringIO
from pathlib import Path

MAX_OPCODE_ARGS = 7
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEFAULT_EXEC_EVMONE = '../../../gas-cost-estimator-clients/build/evmone/evmone-bench'
DEFAULT_EXEC_GETH = '../../../gas-cost-estimator-clients/build/geth/evm'
DEFAULT_EXEC_NETHERMIND = '../../../gas-cost-estimator-clients/build/nethermind/Nethermind.Benchmark.Runner'
DEFAULT_EXEC_ERIGON = '../../../gas-cost-estimator-clients/build/erigon/evm'
DEFAULT_EXEC_REVM = '../../../gas-cost-estimator-clients/build/revm/revme'
DEFAULT_EXEC_ETHERJS = '../../../gas-cost-estimator-clients/build/ethereumjs/index.js'
DEFAULT_EXEC_BESU = '../../../gas-cost-estimator-clients/build/besu/evmtool/bin/evmtool'


class Program(object):
    """
    POD object for a program
    """

    def __init__(self, id, bytecode, measured_op_position):
        self.id = id
        self.bytecode = bytecode
        self.measured_op_position = measured_op_position


class Measurements(object):
    """
    Script to conveniently run instrumentation samples.

    To use together with outputs from the `program_generator/pg_xxx.py` scripts, see docs therein.

    Prints measurement CSV in the following format:
    ```
    | program_id | sample_id | measured_time_ns | remaining measured values ... |

    ```
    """

    def _program_from_csv_row(self, row):
        program_id = row['program_id']
        bytecode = self._expand_unreachable_code(row['bytecode'])

        # might be missing
        measured_op_position = row.get('measured_op_position')
        return Program(program_id, bytecode, measured_op_position)

    def _expand_unreachable_code(self, bytecode):
        if bytecode[-11:] == 'unreachable':
            bytecode = bytecode[:-11]
            bytecode += '00'  # STOP
            # watch out to not hit the hard `MAX_ARG_STRLEN` limit of `131072` chars,
            # c.f. https://tousu.in/qa/?qa=833087/
            bytecode += '03' * ((1 << 11) - len(bytecode) // 2)
            return bytecode
        else:
            return bytecode

    def measure(self, sample_size=1, evm="evmone", input_file="", exec_path=""):
        """
        Main entrypoint of the CLI tool.

        Reads programs' CSV from STDIN. Prints measurement results CSV to STDOUT

        Parameters:
        sample_size (integer): size of a sample to pass into the EVM measuring executable
        mode (string): Measurement mode. Allowed: total, all, trace, benchmark
        evm (string): which evm use. Default: geth. Allowed: geth, evmone
        """

        if (input_file != ""):
            input_file_full_path = os.path.abspath(input_file)
            self._programs = []
            with open(input_file_full_path) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
                for row in reader:
                    # skip if row starts from #
                    if row['program_id'].startswith('#'):
                        continue
                    self._programs.append(self._program_from_csv_row(row))
        else:
            reader = csv.DictReader(sys.stdin, delimiter=',', quotechar='"')
            self._programs = [
                self._program_from_csv_row(row) for row in reader]
        # print("Loaded {} programs".format(len(self._programs)))

        geth = "geth"
        evmone = "evmone"
        nethermind = "nethermind"
        ethereumjs = 'ethereumjs'
        erigon = "erigon"
        revm = "revm"
        besu = "besu"

        allowed_evms = {geth, evmone, nethermind,
                        ethereumjs, erigon, revm, besu}
        if evm not in allowed_evms:
            print("Wrong evm parameter. Allowed are: {}".format(
                ','.join(allowed_evms)))
            return

        header = ""
        if evm == geth or evm == erigon:
            header = "program_id,sample_id,total_time_ns,mem_allocs,mem_alloc_bytes"
        elif evm == evmone:
            header = "program_id,sample_id,total_time_ns,iterations_count"
        elif evm == nethermind:
            header = "program_id,sample_id,total_time_ns,iterations_count,std_dev_time_ns,mem_allocs,mem_alloc_bytes"
        elif evm == ethereumjs or evm == revm:
            header = "program_id,sample_id,total_time_ns,iterations_count,std_dev_time_ns"
        elif evm == besu:
            header = "program_id,sample_id,total_time_ns,iterations_count,std_dev_time_ns,gasUsed,pass"
        print(header)

        for program in self._programs:
            instrumenter_result = None
            if evm == geth:
                instrumenter_result = self.run_geth_benchmark(
                    program, sample_size, exec_path)
            elif evm == evmone:
                instrumenter_result = self.run_evmone_benchmark(
                    program, sample_size, exec_path)
            elif evm == nethermind:
                instrumenter_result = self.run_nethermind_benchmark(
                    program, sample_size, exec_path)
            elif evm == ethereumjs:
                instrumenter_result = self.run_ethereumjs_benchmark(
                    program, sample_size, exec_path)
            elif evm == erigon:
                instrumenter_result = self.run_erigon_benchmark(
                    program, sample_size, exec_path)
            elif evm == revm:
                instrumenter_result = self.run_revm_benchmark(
                    program, sample_size, exec_path)
            elif evm == besu:
                instrumenter_result = self.run_besu_benchmark(
                    program, sample_size, exec_path)

            if instrumenter_result is None:
                return
            result_row = self.csv_row_append_info(instrumenter_result, program)

            csv_chunk = '\n'.join(result_row)
            print(csv_chunk)

    def _parse_geth_benchmark_output(self, output):
        execution_time_pattern = r"execution time:\s*([\d\.]+)(µs|ms)"
        allocations_pattern = r"allocations:\s*([\d\.]+)"
        allocated_bytes_pattern = r"allocated bytes:\s*([\d\.]+)"

        execution_time_match = re.search(execution_time_pattern, output)
        allocations = re.search(allocations_pattern, output)
        allocated_bytes = re.search(allocated_bytes_pattern, output)

        if execution_time_match:
            execution_time = float(execution_time_match.group(1))
            time_unit = execution_time_match.group(2)
            if time_unit == 'µs':  # convert microseconds to nanoseconds
                execution_time *= 1000
            if time_unit == 'ms':  # convert milliseconds to nanoseconds
                execution_time *= 1000000
        else:
            execution_time = None

        allocations = allocations.group(1) if allocations else None

        allocated_bytes = allocated_bytes.group(1) if allocated_bytes else None

        return "{},{},{}".format(int(execution_time), int(allocations), int(allocated_bytes))

    def run_geth_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_GETH)
        else:
            exec_path = os.path.abspath(exec_path)

        args = ['run', '--bench', program.bytecode]
        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(
                invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            _, stderr = pro.communicate()

            instrumenter_result = self._parse_geth_benchmark_output(stderr)

            results.append(str(run_id) + "," + instrumenter_result)
        return results

    def run_nethermind_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(
                DIR_PATH + '/' + DEFAULT_EXEC_NETHERMIND)
        else:
            exec_path = os.path.abspath(exec_path)
        exec_parent = os.path.dirname(exec_path)

        args = ['--mode', 'bytecode', '--bytecode', program.bytecode]

        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(invocation, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, universal_newlines=True, cwd=exec_parent)
            stdout, stderr = pro.communicate()

            if (stderr != ""):
                print("Error in nethermind benchmark")
                print(stderr)
                return

            instrumenter_result = stdout.split('\n')[0]
            results.append(str(run_id) + "," + instrumenter_result)
        return results

    def run_evmone_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_EVMONE)
        else:
            exec_path = os.path.abspath(exec_path)

        if program.bytecode.startswith('0x'):
            bytecode = program.bytecode
        else:
            bytecode = '0x' + program.bytecode

        args = [bytecode, '--benchmark_format=csv']
        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(
                invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = pro.communicate()
            last_line = [line for line in stdout.split('\n') if line][-1]
            result = last_line.split(',')
            results.append(
                f'{run_id},{float(result[2]) * 1000},{result[1]}')

        return results

    def run_erigon_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_ERIGON)
        else:
            exec_path = os.path.abspath(exec_path)

        args = ['--code', program.bytecode, '--bench', 'run']
        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(
                invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            _, stderr = pro.communicate()

            instrumenter_result = self._parse_geth_benchmark_output(stderr)

            results.append(str(run_id) + "," + instrumenter_result)
        return results

    def run_ethereumjs_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_ETHERJS)
        else:
            exec_path = os.path.abspath(exec_path)

        ethereumjs_benchmark = [
            'node',
            # So that garbage collector won't be executed until program eats 4GB of RAM
            '--max-old-space-size=4096',
            exec_path]
        args = ["benchmarks",
                f'bytecode:{sample_size}', "-b", program.bytecode, "--csv"]
        invocation = ethereumjs_benchmark + args
        result = subprocess.run(
            invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the final newline

        raw_result = [line for line in result.stdout.split('\n')[1:] if line]

        instrumenter_result = []
        line_id = 1
        for line in raw_result:
            line_values = line.split(',')
            
            if line_values[2].startswith('±') and line_values[2].endswith('%'):
                std_dev_ns = (float(line_values[2][1:-1]) * float(line_values[1])) / 100
            else :
                std_dev_ns = line_values[2]

            instrumenter_result.append(
                f'{line_id},{line_values[1]},{line_values[3]},{std_dev_ns}')
            line_id += 1
        return instrumenter_result

    def run_revm_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_REVM)
        else:
            exec_path = os.path.abspath(exec_path)

        args = [
            'evm',
            program.bytecode,
            '--bench']
        invocation = [exec_path] + args
        results = []
        for run_id in range(1, sample_size + 1):

            pro = subprocess.Popen(invocation,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdin=subprocess.PIPE,
                                   universal_newlines=True)
            stdout, stderr = pro.communicate(program.bytecode)

            result_line = self._create_revm_result_line(run_id)
            results.append(result_line)

        return results

    def _create_revm_result_line(self, sample_id):
        results_base_folder = os.path.abspath(
            os.getcwd() + '/target/criterion/revme/bytecode')
        base_benchmark_data = json.load(
            open(results_base_folder+'/new/estimates.json'))
        base_benchmark_samples_data = json.load(
            open(results_base_folder+'/new/sample.json'))

        # header = "program_id,sample_id,total_time_ns,iterations_count,std_dev_time_ns"

        iterations = int(sum(base_benchmark_samples_data['iters']))
        sampling_mode = base_benchmark_samples_data['sampling_mode']
        if sampling_mode == 'Linear':
            total_time_ns = int(base_benchmark_data['slope']['point_estimate'])
        elif sampling_mode == 'Flat':
            total_time_ns = int(base_benchmark_data['mean']['point_estimate'])
        else:
            raise ValueError('Unknown sampling mode' + sampling_mode)
        columns = [
            sample_id,  # sample_id
            total_time_ns,  # total_time_ns
            iterations,  # iterations_count
            # engine_overhead_time_ns
            round(base_benchmark_data['std_dev']
                  ['point_estimate'], 2),  # std_dev_time_ns
        ]

        shutil.rmtree(results_base_folder, True)

        return ','.join(str(col) for col in columns)

    def run_besu_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_BESU)
        else:
            exec_path = os.path.abspath(exec_path)

        args = [ '--code=' + program.bytecode, '--repeat=1000', '--samples=1000' ]
        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(invocation, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = pro.communicate()

            if (stderr != ""):
                print("Error in besu benchmark")
                print(stderr)
                return

            stdout_lines = stdout.splitlines()
            # besu warnings, do not break execution but go to stderr
            for i in range(0, len(stdout_lines) - 2):
                print(stdout_lines[i], file=sys.stderr)

            try:
                result = json.loads(stdout_lines[-1])
            except:
                print("Error parsing the result:", stdout_lines[-1])
                return

            results.append(
                f'{run_id},{str(result["timens"])},{10*100},{str(result["std_dev_timens"])},{result["gasUsed"]},{result["pass"]}')
        return results

    def csv_row_append_info(self, instrumenter_result, program):
        # append program_id which are not known to the instrumenter tool
        to_append = "{},".format(program.id)
        return [to_append + row for row in instrumenter_result]


def main():
    fire.Fire(Measurements, name='measure')
    # print('Running measurements...')
    # fire.Fire(Measurements, name='measure', command='measure')
    # print('Done')


if __name__ == '__main__':
    main()
