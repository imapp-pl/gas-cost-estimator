import csv
import fire
import sys
import subprocess
import os.path

MAX_OPCODE_ARGS=7

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

  To use together with outputs rom the `program_generator.py`, see docs therein.

  Prints measurement CSV in the following format:
  ```
  | program_id | sample_id | run_id | instruction_id | measure_all_time_ns | measure_one_time_ns |
  ```

  Expects the EVM measuring executable (e.g. our `src/instrumentation_measurement/geth/main.go`) to provide
  a chunk of this CSV of the format (without header!):
  | run_id | instruction_id | measure_all_time_ns | measure_one_time_ns |
  """

  def _program_from_csv_row(self, row):
    program_id = row['program_id']
    bytecode = row['bytecode']

    # might be missing
    measured_op_position = row.get('measured_op_position')
    return Program(program_id, bytecode, measured_op_position)

  def __init__(self):
    reader = csv.DictReader(sys.stdin, delimiter=',', quotechar='"')
    self._programs = [self._program_from_csv_row(row) for row in reader]

  def measure(self, sampleSize, mode="all", evm="geth", nSamples=1):
    """
    Main entrypoint of the CLI tool.

    Reads programs' CSV from STDIN. Prints measurement results CSV to STDOUT

    Parameters:
    sampleSize (integer): size of a sample to pass into the EVM measuring executable
    evm (string): which evm use. Default: geth. Allowed: geth, openethereum, evmone
    nSamples (integer): number of samples (individual starts of the EVM measuring executable) to do
    mode (string): Measurement mode. Allowed: total, all, trace
    """

    geth = "geth"
    openethereum = "openethereum"
    openethereum_ewasm = "openethereum_ewasm"
    evmone = "evmone"

    measure_total = "total"
    measure_all = "all"
    trace_opcodes = "trace"


    if evm not in {geth, openethereum, evmone, openethereum_ewasm}:
      print("Wrong evm parameter. Allowed are: {}, {}, {}, {}".format(geth, openethereum, evmone, openethereum_ewasm))
      return

    if mode not in {measure_total, measure_all, trace_opcodes}:
        print("Invalid measurement mode. Allowed options: {}, {}, {}".format(measure_total, measure_all, trace_opcodes))
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


    for program in self._programs:
      for sample_id in range(nSamples):
        instrumenter_result = None
        if evm == geth:
          instrumenter_result = self.run_geth(mode, program, sampleSize)
        elif evm == openethereum:
          instrumenter_result = self.run_openethereum(mode, program, sampleSize)
        elif evm == openethereum_ewasm:
          instrumenter_result = self.run_openethereum_wasm(program, sampleSize)
        elif evm == evmone:
          instrumenter_result = self.run_evmone(mode, program, sampleSize)

        if mode == trace_opcodes:
            instrumenter_result = self.sanitize_tracer_result(instrumenter_result)


        result_row = self.csv_row_append_info(instrumenter_result, program, sample_id)

        csv_chunk = '\n'.join(result_row)
        print(csv_chunk)

  def run_geth(self, mode, program, sampleSize):
    golang_main = ['go', 'run', './instrumentation_measurement/geth/main.go']
    args = ['--mode', mode, '--printCSV', '--printEach=false', '--sampleSize={}'.format(sampleSize)]
    bytecode_arg = ['--bytecode', program.bytecode]
    invocation = golang_main + args + bytecode_arg
    result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0
    # strip the final newline
    instrumenter_result = result.stdout.split('\n')[:-1]

    return instrumenter_result

  def run_openethereum(self, mode, program, sampleSize):
    openethereum_build_path = './instrumentation_measurement/openethereum/target/release/'
    openethereum_main = [openethereum_build_path + 'openethereum-evm']
    args = ['--measure-mode', mode, '--code', program.bytecode, "--repeat", "{}".format(sampleSize)]
    invocation = openethereum_main + args
    result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0
    # strip the output normally printed by openethereum ("output", gas used, time info)
    instrumenter_result = result.stdout.split('\n')[:-4]
    return instrumenter_result

  def run_openethereum_wasm(self, program, sampleSize):
    openethereum_path = './instrumentation_measurement/openethereum'
    openethereum_build_path = os.path.join(openethereum_path, 'target/release/')
    openethereum_main = [openethereum_build_path + 'openethereum-evm']
    chain = os.path.join(openethereum_path, 'ethcore/res/instant_seal.json')
    args = ['--code', program.bytecode, "--repeat", "{}".format(sampleSize), "--chain", chain, "--gas", "5000"]
    invocation = openethereum_main + args
    result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0
    # strip the output normally printed by openethereum ("output", gas used, time info)
    # also, when executing ewasm bytecode, OpenEthereum first runs some EVM code (38 instructions)
    instrumenter_result = result.stdout.split('\n')[38:-4]
    return instrumenter_result

  def run_evmone(self, mode, program, sampleSize):
    evmone_build_path = './instrumentation_measurement/evmone/build/'
    evmone_main = [evmone_build_path + 'evmc/bin/evmc', 'run']
    args = ['--measure-{}'.format(mode),'--vm', evmone_build_path + '/lib/libevmone.so', '--repeat', '{}'.format(sampleSize)]
    invocation = evmone_main + args + [program.bytecode]
    result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0
    # strip additional output information added by evmone
    instrumenter_result = result.stdout.split('\n')[2:-5]

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
        prefix = row[0:4] # take first columns untouched
        opcode = row[2]
        stack_depth = int(row[3])
        stack = row[4:]

        # stack top is stack[stack_depth - 1] and stack bottom is stack[0],
        # so to take some deeper arguments we have to do some mysterious maths
        args = [stack[stack_depth - arg_depth - 1] for arg_depth in specs[opcode]]

        # append with empty positions to conform to CSV format
        for i in range(len(args), MAX_OPCODE_ARGS):
            args.append('')

        parsed_line = ','.join(prefix + args)
        result.append(parsed_line)

      return result

  def read_opcodes_specs(self):
      with open('./instrumentation_measurement/data/opcodes_args.csv', newline='') as opcodes_args_file:
        args_keys = list('arg{}_depth'.format(i) for i in range(6))
        reader = csv.DictReader(opcodes_args_file, delimiter=',', quotechar='"')

        specs = {}
        for row in reader:
          args = []
          opcode = row['mnemonic']
          for k in args_keys:
              if row[k] != '' and row[k] != None:
                  args.append(int(row[k]))
          specs[opcode] = args
        return specs


def main():
  fire.Fire(Measurements, name='measure')

if __name__ == '__main__':
  main()
