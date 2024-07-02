import csv
import fire
import json
import os.path
import re
import sys
import subprocess
from io import StringIO
from pathlib import Path

MAX_OPCODE_ARGS = 7
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

CLOCKSOURCE_PATH = '/sys/devices/system/clocksource/clocksource0/current_clocksource'
DEFAULT_EXEC_GETH = '../../../gas-cost-estimator-clients/build/geth/evm'
DEFAULT_EXEC_NETHERMIND = '../../../gas-cost-estimator-clients/build/nethermind/Nethermind.Benchmark.Runner'
DEFAULT_EXEC_ERIGON = '../../../gas-cost-estimator-clients/build/erigon/evm'
DEFAULT_EXEC_ETHJS = '../../../gas-cost-estimator-clients/build/ethereumjs-monorepo/packages/vm'
DEFAULT_EXEC_REVM = '../../../gas-cost-estimator-clients/build/revm-orignal/revm/crates/revm/Cargo.toml'


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
    | program_id | sample_id | run_id | instruction_id | measure_all_time_ns | measure_all_timer_time_ns |
    ```
    or
    ```
    | program_id | sample_id | run_id | measure_total_time_ns | measure_total_timer_time_ns |
    ```
    Depending on the `mode` parameter.

    Expects the EVM measuring executable (e.g. our `src/instrumentation_measurement/geth/main.go`) to provide
    a chunk of this CSV of the format (without header!):
    | run_id | instruction_id | measure_all_time_ns | measure_all_timer_time_ns |
    or
    | run_id | measure_total_time_ns | measure_total_timer_time_ns |

    There is also a special `mode` parameter value: `trace`, which produces a CSV in the following format:
    ```
    | program_id | sample_id | instruction_id | pc | op | stack_depth | arg_0 | arg_... |
    ```
    """

    # def __init__(self):

    #     # parser = argparse.ArgumentParser(description='Measure EVM bytecode')
    #     # parser.add_argument('--mode', type=str, default='benchmark', help='Measurement mode. Allowed: total, all, trace, benchmark')

    #     print(DIR_PATH)

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

    def measure(self, sample_size=1, mode="all", evm="geth", n_samples=1, input_file="", exec_path=""):
        """
        Main entrypoint of the CLI tool.

        Reads programs' CSV from STDIN. Prints measurement results CSV to STDOUT

        Parameters:
        sample_size (integer): size of a sample to pass into the EVM measuring executable
        mode (string): Measurement mode. Allowed: total, all, trace, benchmark
        evm (string): which evm use. Default: geth
        n_samples (integer): number of samples (individual starts of the EVM measuring executable) to do
        """

        if (input_file != ""):
            input_file_full_path = os.path.abspath(input_file)
            self._programs = []
            with open(input_file_full_path) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
                for row in reader:
                    self._programs.append(self._program_from_csv_row(row))
        else:
            reader = csv.DictReader(sys.stdin, delimiter=',', quotechar='"')
            self._programs = [self._program_from_csv_row(row) for row in reader]
    
        geth = "geth"
        evmone = "evmone"
        nethermind = "nethermind"
        ethereumjs = "ethereumjs"
        erigon = "erigon"
        revm = "revm"

        measure_total = "total"
        measure_all = "all"
        trace_opcodes = "trace"
        measure_perf = "perf"
        measure_time = "time"
        benchmark_mode = "benchmark"

        allowed_evms = {geth, evmone, nethermind, ethereumjs, erigon, revm}
        if evm not in allowed_evms:
            print("Wrong evm parameter. Allowed are: {}".format(','.join(allowed_evms)))
            return

        if mode not in {measure_total, measure_all, trace_opcodes, measure_perf, measure_time, benchmark_mode}:
            print("Invalid measurement mode. Allowed options: {}, {}, {}, {}, {}, {}"
                  .format(measure_total, measure_all, trace_opcodes, measure_perf, measure_time, benchmark_mode))
            return
        elif mode == measure_total:
            header = "program_id,sample_id,run_id,measure_total_time_ns,measure_total_timer_time_ns"
            print(header)
        elif mode == measure_all:
            header = "program_id,sample_id,run_id,instruction_id,measure_all_time_ns,measure_all_timer_time_ns"
            print(header)
        elif mode == trace_opcodes:
            header = "program_id,sample_id,instruction_id,pc,op,stack_depth"
            for i in range(MAX_OPCODE_ARGS):
                elem = ",arg_{}".format(i)
                header += elem
            print(header)
        elif mode == benchmark_mode:
            if evm == geth:
                header = "program_id,sample_id,run_id,total_time_ns,mem_allocs_count,mem_allocs_bytes"
            elif evm == nethermind:
                header = "program_id,sample_id,run_id,iterations_count,engine_overhead_time_ns,execution_loop_time_ns,total_time_ns,std_dev_time_ns,mem_allocs_count,mem_allocs_bytes"
            elif evm == ethereumjs:
                header = "program_id,sample_id,run_id,iterations_count,engine_overhead_time_ns,execution_loop_time_ns,total_time_ns,std_dev_time_ns"
            elif evm == erigon:
                header = "program_id,sample_id,run_id,total_time_ns,mem_allocs_count,mem_allocs_bytes"
            elif evm == revm:
                header = "program_id,sample_id,run_id,iterations_count,engine_overhead_time_ns,execution_loop_time_ns,total_time_ns,std_dev_time_ns"
            print(header)
        elif mode == measure_perf:
            header = "program_id,sample_id,task_clock,context_switches,page_faults,instructions,branches,branch_misses,L1_dcache_loads,LLC_loads,LLC_load_misses,L1_icache_loads,L1_icache_load_misses,dTLB_loads,dTLB_load_misses,iTLB_loads,iTLB_load_misses"
            print(header)
        elif mode == measure_time:
            header = "program_id,sample_id,real_time_perf,user_time_perf,sys_time_perf,real_time_pure,user_time_pure,sys_time_pure"
            print(header)

        for program in self._programs:
            for sample_id in range(n_samples):
                instrumenter_result = None
                if evm == geth:
                    if mode == benchmark_mode:
                        instrumenter_result = self.run_geth_benchmark(program, sample_size, exec_path)
                elif evm == evmone:
                    instrumenter_result = self.run_evmone(mode, program, sample_size)
                elif evm == nethermind:
                    if mode == benchmark_mode:
                        instrumenter_result = self.run_nethermind_benchmark(program, sample_size, exec_path)
                    else:
                        instrumenter_result = self.run_nethermind(program, sample_size)
                elif evm == ethereumjs and mode == benchmark_mode:
                    instrumenter_result = self.run_ethereumjs_benchmark(program, sample_size)               
                elif evm == erigon:
                    if mode == benchmark_mode:
                        instrumenter_result = self.run_erigon_benchmark(program, sample_size, exec_path)
                elif evm == revm and mode == benchmark_mode:
                    instrumenter_result = self.run_revm_benchmark(program, sample_size, exec_path)

                if mode == trace_opcodes:
                    instrumenter_result = self.sanitize_tracer_result(instrumenter_result)

                result_row = self.csv_row_append_info(instrumenter_result, program, sample_id)

                csv_chunk = '\n'.join(result_row)
                print(csv_chunk)

    def _parse_geth_benchmark_output(self, stdout, stderr):
        text = stderr

        execution_time_pattern = r"execution time:\s*([\d\.]+)(µs|ms)"
        allocations_pattern = r"allocations:\s*([\d\.]+)"
        allocated_bytes_pattern = r"allocated bytes:\s*([\d\.]+)"

        execution_time_match = re.search(execution_time_pattern, text)
        allocations = re.search(allocations_pattern, text)
        allocated_bytes = re.search(allocated_bytes_pattern, text)

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
            exec_path = os.path.abspath(DIR_PATH +'/'+ DEFAULT_EXEC_GETH)
        else:
            exec_path = os.path.abspath(exec_path)

        args = ['--code', program.bytecode, '--bench', 'run']
        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = pro.communicate()

            instrumenter_result = self._parse_geth_benchmark_output(stdout, stderr)

            results.append(str(run_id) + "," + instrumenter_result)
        return results

    def run_nethermind(self, program, sample_size):
        geth_benchmark = [
            './instrumentation_measurement/nethermind_benchmark/src/Nethermind/Imapp.Measurement.Runner/bin/Release/net6.0/Imapp.Measurement.Runner']
        args = ['--bytecode', program.bytecode, '--print-csv', '--sample-size={}'.format(sample_size)]
        invocation = geth_benchmark + args
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the final newline
        instrumenter_result = result.stdout.split('\n')[:-1]
        return instrumenter_result

    def run_nethermind_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH +'/'+ DEFAULT_EXEC_NETHERMIND)
        else:
            exec_path = os.path.abspath(exec_path)
        exec_parent = os.path.dirname(exec_path)

        args = ['--mode', 'bytecode', '--bytecode', program.bytecode]

        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=exec_parent)
            stdout, stderr = pro.communicate()

            if (stderr != ""):
                print("Error in nethermind benchmark")
                print(stderr)
                return
            
            instrumenter_result = stdout.split('\n')[0]
            results.append(str(run_id) + "," + instrumenter_result)
        return results

    def run_evmone(self, mode, program, sampleSize):
        if mode == 'perf':
            return self.run_perf_evmone(program)
        elif mode == 'time':
            return self.run_time_evmone(program)
        else:
            return self.run_evmone_default(mode, program, sampleSize)

    def run_perf_evmone(self, program):
        evmone_build_path = './instrumentation_measurement/build/'
        bin = evmone_build_path + 'bin/evmc'
        vm = evmone_build_path + 'lib/libevmone.so'
        perf_evmone_main = ['perf', 'stat', '-ddd', '-x', ',', bin, 'run']
        #    perf_evmone_main = ['perf', 'stat', '--event', 'task-clock:D,instructions:D', '-x', ',', bin, 'run']
        args = ['--vm', vm]
        bytecode = program.bytecode
        invocation = perf_evmone_main + args + [bytecode]

        result = subprocess.run(invocation, capture_output=True, universal_newlines=True)
        # print('error', result.stderr)
        assert result.returncode == 0
        instrumenter_result = ''
        perf_stats = csv.reader(StringIO(result.stderr), delimiter=',')
        for row in perf_stats:
            event_name = row[2]
        if (event_name in ['task-clock', 'context-switches', 'page-faults', 'instructions', 'branches', 'branch-misses', 'L1-dcache-loads', 'LLC-loads', 'LLC-load-misses', 'L1-icache-loads', 'L1-icache-load-misses', 'dTLB-loads', 'dTLB-load-misses', 'iTLB-loads', 'iTLB-load-misses']):
            instrumenter_result += row[0] + ','
        # strip the final comma
        instrumenter_result = instrumenter_result[:-1]

        return [instrumenter_result]

    def run_time_evmone(self, program):
        evmone_build_path = './instrumentation_measurement/build/'
        bin = evmone_build_path + 'bin/evmc'
        vm = evmone_build_path + 'lib/libevmone.so'
        perf_evmone_main = ['time', '-p', 'perf', 'stat', '-ddd', '-x', ',', bin, 'run']
        pure_evmone_main = ['time', '-p', bin, 'run']
        args = ['--vm', vm]
        bytecode = program.bytecode
        perf_invocation = perf_evmone_main + args + [bytecode]
        pure_invocation = pure_evmone_main + args + [bytecode]

        instrumenter_result = ''
        result = subprocess.run(perf_invocation, capture_output=True, universal_newlines=True)
        # print('error', result.stderr)
        assert result.returncode == 0
        perf_stats = result.stderr.split('\n')
        len_perf_stats = len(perf_stats) - 1
        instrumenter_result += perf_stats[len_perf_stats-3].split(' ')[1] + ',' + perf_stats[len_perf_stats-2].split(' ')[1] + ',' + perf_stats[len_perf_stats-1].split(' ')[1]

        instrumenter_result += ','
        result = subprocess.run(pure_invocation, capture_output=True, universal_newlines=True)
        # print('error', result.stderr)
        assert result.returncode == 0
        pure_stats = result.stderr.split('\n')
        len_pure_stats = len(pure_stats) - 1
        instrumenter_result += pure_stats[len_pure_stats-3].split(' ')[1] + ',' + pure_stats[len_pure_stats-2].split(' ')[1] + ',' + pure_stats[len_pure_stats-1].split(' ')[1]

        return [instrumenter_result]

    def run_evmone_default(self, mode, program, sample_size):
        evmone_build_path = './instrumentation_measurement/evmone/build/'
        bin = evmone_build_path + 'bin/evmc'
        vm = evmone_build_path + 'lib/libevmone.so'
        evmone_build_path = './instrumentation_measurement/evmone/build/'
        evmone_main = [evmone_build_path + 'bin/evmc', 'run']

        # only measure-total is currently supported
        assert mode == "total"
        args = ['--vm', evmone_build_path + '/lib/libevmone.so,O=0', '--sample-size', '{}'.format(sample_size)]
        invocation = evmone_main + args + [program.bytecode]
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip additional output information added by evmone
        instrumenter_result = result.stdout.split('\n')[3:-4]
                                    

        return instrumenter_result

    def run_erigon_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH +'/'+ DEFAULT_EXEC_ERIGON)
        else:
            exec_path = os.path.abspath(exec_path)

        args = ['--code', program.bytecode, '--bench', 'run']
        invocation = [exec_path] + args

        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = pro.communicate()

            instrumenter_result = self._parse_geth_benchmark_output(stdout, stderr)

            results.append(str(run_id) + "," + instrumenter_result)
        return results

    def run_ethereumjs_benchmark(self, program, sample_size):
        ethereumjs_benchmark = [
            'node',
            '-max-old-space-size=4096',  # So that garbage collector won't be executed until program eats 4GB of RAM
            DEFAULT_EXEC_ETHJS + "/benchmarks/run.js",
            "benchmarks",
            "bytecode:10"]
        args = ['-b', program.bytecode]
        invocation = ethereumjs_benchmark + args
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the final newline
        instrumenter_result = result.stdout.split('\n')[:-1]
        return instrumenter_result

    def run_revm_benchmark(self, program, sample_size, exec_path):
        if exec_path == "":
            exec_path = os.path.abspath(DIR_PATH + '/' + DEFAULT_EXEC_REVM)
        else:
            exec_path = os.path.abspath(exec_path)

        revm_benchmark = [
            'cargo',
            'bench',
            '--bench=criterion_bytecode',
        ]
        args = [
            '--manifest-path=' + exec_path,
            '--',
            '--noplot']
        invocation = revm_benchmark + args
        print(' '.join(invocation))
        results = []
        for run_id in range(1, sample_size + 1):
            pro = subprocess.Popen(
                invocation, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
            print("starting")
            std, err = pro.communicate(program.bytecode)
            print(std)
            print(err)
            result_line = self._create_revm_result_line(run_id, exec_path)
            print(result_line)
            results.append(result_line)
        return results

    def _create_revm_result_line(self, run_id, exec_path):
        results_base_folder = os.path.abspath(Path(exec_path) / '../../../target/criterion/bytecode')
        base_benchmark_data = json.load(open(results_base_folder + '/bytecode-benchmark/new/estimates.json'))
        base_benchmark_samples_data = json.load(open(results_base_folder + '/bytecode-benchmark/new/sample.json'))
        stop_benchmark_data = json.load(open(results_base_folder + '/bytecode-benchmark-stop/new/estimates.json'))

        iterations = int(sum(base_benchmark_samples_data['iters']))
        columns = [
            run_id,  # run_id
            iterations,  # iterations_count
            int(stop_benchmark_data['slope']['point_estimate']),  # engine_overhead_time_ns
            # execution_loop_time_ns
            int(base_benchmark_data['slope']['point_estimate'] - stop_benchmark_data['slope']['point_estimate']),
            int(base_benchmark_data['slope']['point_estimate']),  # total_time_ns
            round(base_benchmark_data['std_dev']['point_estimate'], 2),  # std_dev_time_ns
        ]
        return ','.join(str(col) for col in columns)

    def csv_row_append_info(self, instrumenter_result, program, sample_id):
        # append program_id and sample_id which are not known to the instrumenter tool
        to_append = "{},{},".format(program.id, sample_id)
        return [to_append + row for row in instrumenter_result]

    def sanitize_tracer_result(self, tracer_result):
        specs = self.read_opcodes_specs()

        result = []
        for row in tracer_result:
            row = row.split(',')
            prefix = row[0:4]  # take first columns untouched
            opcode = row[2]
            stack_depth = int(row[3])
            stack = row[4:]

            args = None
            match_result = re.search(r'^(DUP|PUSH|SWAP)([1-9][0-9]?)$', opcode)
            if match_result is None:
                # stack top is stack[stack_depth - 1] and stack bottom is stack[0],
                # so to take some deeper arguments we have to do some mysterious maths
                arity = specs[opcode]
                args = stack[stack_depth - (arity - 1) - 1: stack_depth]
            else:
                (opcode, opcode_variant) = match_result.groups()
                opcode_variant = int(opcode_variant)
                if opcode == 'PUSH':
                    args = []
                elif opcode == 'DUP':
                    args = [stack[stack_depth - (opcode_variant - 1) - 1]]
                elif opcode == 'SWAP':
                    args = [stack[stack_depth - opcode_variant - 1], stack[stack_depth - 1]]

            # since it is more natural to read args left->right
            # and stack is quite the opposite
            # lets reverse the args
            args.reverse()

            # append with empty positions to conform to CSV format
            for i in range(len(args), MAX_OPCODE_ARGS):
                args.append('')

            parsed_line = ','.join(prefix + args)
            result.append(parsed_line)

        return result

    def read_opcodes_specs(self):
        opcodes_file = os.path.join(DIR_PATH, '..', 'program_generator', 'data', 'opcodes.csv')
        with open(opcodes_file, newline='') as opcodes_args_file:
            reader = csv.DictReader(opcodes_args_file, delimiter=',', quotechar='"')
            specs = dict()
            for row in reader:
                opcode = row['Mnemonic']
                if re.search(r'^(SWAP|DUP|PUSH|INVALID).*$', opcode) is None:
                    # "Removed from stack" ~ opcode arity
                    specs[opcode] = int(row['Removed from stack'])
            return specs

def main():
    fire.Fire(Measurements, name='measure')
    # print('Running measurements...')
    # fire.Fire(Measurements, name='measure', command='measure')
    # print('Done')

if __name__ == '__main__':
    main()
