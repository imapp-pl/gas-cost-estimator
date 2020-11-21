import csv
import fire
import sys
import subprocess

# TODO: uncopy-paste from program_generator.py
class Program(object):
  """
  POD object for a program
  """

  def __init__(self, id, bytecode, measured_op_position):
    self.bytecode = bytecode
    self.measured_op_position = measured_op_position
    self.id = id


class Measurements(object):
  """
  Script to conveniently run instrumentation samples
  """

  # TODO! this is incredibly dirty, needs tidying

  def __init__(self):
    reader = csv.DictReader(sys.stdin, delimiter=',', quotechar='"')
    self._programs = [Program(i['opcode_measured'], i['bytecode'], int(i['measured_op_position'])) for i in reader]

  def measure(self):
    """
    Main entrypoint of the CLI tool. Reads programs' CSV from STDIN
    """
    header = "program_id,sample_id,run_id,instruction_id,measure_all_time_ns,measure_one_time_ns"
    print(header)

    for program in self._programs:
      golang_main = ['go', 'run', './instrumentation_measurement/geth/main.go']
      args = ['--printCSV', '--printEach=false', '--sampleSize=50']
      bytecode_arg = ['--bytecode', program.bytecode]
      invocation = golang_main + args + bytecode_arg
      result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
      assert result.returncode == 0
      instrumenter_result = result.stdout.split('\n')[:-1]
      to_append = "{},{},".format(program.id, 0)
      instrumenter_result = [to_append + row for row in instrumenter_result]

      # temporarily hack this like that to have some nice graphs
      # TODO unhack
      n_measurements = len(instrumenter_result)
      n_instructions = n_measurements // 50
      instrumenter_result = instrumenter_result[program.measured_op_position::n_instructions]
      instrumenter_result = '\n'.join(instrumenter_result)

      # append program_id and sample_id which are not known to the instrumenter tool
      print(instrumenter_result)


def main():
  fire.Fire(Measurements, name='measure')

if __name__ == '__main__':
  main()
