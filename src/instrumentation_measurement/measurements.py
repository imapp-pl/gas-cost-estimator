import csv
import fire
import sys
import subprocess
import re
import os.path

MAX_OPCODE_ARGS = 7
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

CLOCKSOURCE_PATH = '/sys/devices/system/clocksource/clocksource0/current_clocksource'


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

    def _expand_unreachable_code(self, bytecode):
        if bytecode[-11:] == 'unreachable':
            bytecode = bytecode[:-11]
            bytecode += '00'  # STOP
            # watch out to not hit the hard `MAX_ARG_STRLEN` limit of `131072` chars,
            # c.f. https://tousu.in/qa/?qa=833087/
            bytecode += '03' * ((1 << 15) - len(bytecode) // 2)
            return bytecode
        else:
            return bytecode

    def _program_from_csv_row(self, row):
        program_id = row['program_id']
        bytecode = self._expand_unreachable_code(row['bytecode'])

        # might be missing
        measured_op_position = row.get('measured_op_position')
        return Program(program_id, bytecode, measured_op_position)

    def _check_clocksource(self):
        with open(CLOCKSOURCE_PATH) as clocksource:
            return clocksource.readlines() == ['tsc\n']

    def __init__(self):
        reader = csv.DictReader(sys.stdin, delimiter=',', quotechar='"')
        self._programs = [self._program_from_csv_row(row) for row in reader]

    def measure(self, sample_size=1, mode="all", evm="geth", n_samples=1):
        """
        Main entrypoint of the CLI tool.

        Reads programs' CSV from STDIN. Prints measurement results CSV to STDOUT

        Parameters:
        sample_size (integer): size of a sample to pass into the EVM measuring executable
        mode (string): Measurement mode. Allowed: total, all, trace
        evm (string): which evm use. Default: geth. Allowed: geth, openethereum, evmone
        n_samples (integer): number of samples (individual starts of the EVM measuring executable) to do
        """

        geth = "geth"
        openethereum = "openethereum"
        openethereum_ewasm = "openethereum_ewasm"
        evmone = "evmone"
        nethermind = "nethermind"

        measure_total = "total"
        measure_all = "all"
        trace_opcodes = "trace"
        benchmark_mode = "benchmark"

        if not self._check_clocksource():
            print("clocksource should be tsc, found something different. See docker_timer.md somewhere in the docs")
            return

        if evm not in {geth, openethereum, evmone, openethereum_ewasm, nethermind}:
            print("Wrong evm parameter. Allowed are: {}, {}, {}, {}".format(geth, openethereum, evmone,
                                                                            openethereum_ewasm, nethermind))
            return

        if mode not in {measure_total, measure_all, trace_opcodes, benchmark_mode}:
            print("Invalid measurement mode. Allowed options: {}, {}, {}".format(measure_total, measure_all,
                                                                                 trace_opcodes, benchmark_mode))
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
                header = "program_id,sample_id,run_id,iterations_count,engine_overhead_time_ns,execution_loop_time_ns,total_time_ns,mem_allocs_count,mem_allocs_bytes"
            elif evm == nethermind:
                header = "program_id,sample_id,run_id,iterations_count,engine_overhead_time_ns,execution_loop_time_ns,total_time_ns,std_dev_time_ns,mem_allocs_count,mem_allocs_bytes"
            print(header)

        for program in self._programs:
            for sample_id in range(n_samples):
                instrumenter_result = None
                if evm == geth:
                    if mode == benchmark_mode:
                        instrumenter_result = self.run_geth_benchmark(program, sample_size)
                    else:
                        instrumenter_result = self.run_geth(mode, program, sample_size)
                elif evm == openethereum:
                    instrumenter_result = self.run_openethereum(mode, program, sample_size)
                elif evm == openethereum_ewasm:
                    instrumenter_result = self.run_openethereum_wasm(program, sample_size)
                elif evm == evmone:
                    instrumenter_result = self.run_evmone(mode, program, sample_size)
                elif evm == nethermind:
                    if mode == benchmark_mode:
                        instrumenter_result = self.run_nethermind_benchmark(program, sample_size)
                    else:
                        instrumenter_result = self.run_nethermind(program, sample_size)

                if mode == trace_opcodes:
                    instrumenter_result = self.sanitize_tracer_result(instrumenter_result)

                result_row = self.csv_row_append_info(instrumenter_result, program, sample_id)

                csv_chunk = '\n'.join(result_row)
                print(csv_chunk)

    def run_geth(self, mode, program, sample_size):
        golang_main = ['./instrumentation_measurement/bin/geth_main']
        args = ['--mode', mode, '--printCSV', '--printEach=false', '--sampleSize={}'.format(sample_size)]
        bytecode_arg = ['--bytecode', program.bytecode]
        invocation = golang_main + args + bytecode_arg
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the final newline
        instrumenter_result = result.stdout.split('\n')[:-1]
        return instrumenter_result

    def run_geth_benchmark(self, program, sample_size):
        geth_benchmark = ['./instrumentation_measurement/geth_benchmark/tests/imapp_benchmark/imapp_benchmark']

        args = ['--sampleSize', '{}'.format(sample_size)]
        bytecode_arg = ['--bytecode', program.bytecode]
        invocation = geth_benchmark + args + bytecode_arg
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the final newline
        instrumenter_result = result.stdout.split('\n')[:-1]
        return instrumenter_result

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

    def run_nethermind_benchmark(self, program, sample_size):
        geth_benchmark = [
            './instrumentation_measurement/nethermind_benchmark/src/Nethermind/Imapp.Benchmark.Runner/bin/Release/net6.0/Imapp.Benchmark.Runner']
        args = ['--bytecode', program.bytecode, '--print-csv', '--sample-size={}'.format(sample_size)]
        invocation = geth_benchmark + args
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the final newline
        instrumenter_result = result.stdout.split('\n')[:-1]
        return instrumenter_result

    def run_openethereum(self, mode, program, sample_size):
        openethereum_build_path = './instrumentation_measurement/openethereum/target/release/'
        openethereum_main = [openethereum_build_path + 'openethereum-evm']
        args = ['--chain', 'Berlin', '--measure-mode', mode, '--code', program.bytecode, "--repeat",
                "{}".format(sample_size)]
        invocation = openethereum_main + args
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the output normally printed by openethereum ("output", gas used, time info)
        instrumenter_result = result.stdout.split('\n')[:-4]
        return instrumenter_result

    def run_openethereum_wasm(self, program, sample_size):
        openethereum_path = './instrumentation_measurement/openethereum'
        openethereum_build_path = os.path.join(openethereum_path, 'target/release/')
        openethereum_main = [openethereum_build_path + 'openethereum-evm']
        chain = os.path.join(openethereum_path, 'ethcore/res/instant_seal.json')
        args = ['--code', program.bytecode, "--repeat", "{}".format(sample_size), "--chain", chain, "--gas", "5000"]
        invocation = openethereum_main + args
        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0
        # strip the output normally printed by openethereum ("output", gas used, time info)
        # also, when executing ewasm bytecode, OpenEthereum first runs some EVM code (38 instructions)
        instrumenter_result = result.stdout.split('\n')[38:-4]
        return instrumenter_result

    def run_evmone(self, mode, program, sample_size):
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
            if match_result == None:
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


if __name__ == '__main__':
    main()
