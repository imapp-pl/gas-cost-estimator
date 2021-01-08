import csv
import fire
import sys
import subprocess

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

  def __init__(self):
    reader = csv.DictReader(sys.stdin, delimiter=',', quotechar='"')
    self._programs = [Program(i['program_id'], i['bytecode'], int(i['measured_op_position'])) for i in reader]

  def measure(self, sampleSize, evm="geth", nSamples=1):
    """
    Main entrypoint of the CLI tool.

    Reads programs' CSV from STDIN. Prints measurement results CSV to STDOUT

    Parameters:
    sampleSize (integer): size of a sample to pass into the EVM measuring executable
    evm (string): which evm use. Default: geth. Allowed: geth, openethereum
    nSamples (integer): number of samples (individual starts of the EVM measuring executable) to do
    """
    header = "program_id,sample_id,run_id,instruction_id,measure_all_time_ns,measure_one_time_ns"
    print(header)

    geth = "geth"
    openethereum = "openethereum"

    if evm not in {geth, openethereum}:
      print("Wrong evm parameter. Allowed are: {}, {}".format(geth, openethereum))
      return

    for program in self._programs:
      for sample_id in range(nSamples):
        instrumenter_result = None
        if evm == geth:
          instrumenter_result = self.run_geth(program, sampleSize)
        elif evm == openethereum:
          instrumenter_result = self.run_openethereum(program, sampleSize)
        result_row = self.csv_row_append_info(instrumenter_result, program, sample_id)

        csv_chunk = '\n'.join(result_row)
        print(csv_chunk)

  def run_geth(self, program, sampleSize):
    golang_main = ['go', 'run', './instrumentation_measurement/geth/main.go']
    args = ['--printCSV', '--printEach=false', '--sampleSize={}'.format(sampleSize)]
    bytecode_arg = ['--bytecode', program.bytecode]
    invocation = golang_main + args + bytecode_arg
    result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0
    instrumenter_result = result.stdout.split('\n')[:-1]

    return instrumenter_result

  def run_openethereum(self, program, sampleSize):
    openethereum_build_path = './instrumentation_measurement/openethereum/target/release/'
    openethereum_main = [openethereum_build_path + 'openethereum-evm']
    args = ['--code', program.bytecode, "--repeat", "{}".format(sampleSize)]
    invocation = openethereum_main + args
    result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0
    # strip the output normally printed by openethereum ("output", gas used, time info)
    instrumenter_result = result.stdout.split('\n')[:-4]

    return instrumenter_result

  def csv_row_append_info(self, instrumenter_result, program, sample_id):
    # append program_id and sample_id which are not known to the instrumenter tool
    to_append = "{},{},".format(program.id, sample_id)
    return [to_append + row for row in instrumenter_result]


def main():
  fire.Fire(Measurements, name='measure')

if __name__ == '__main__':
  main()
