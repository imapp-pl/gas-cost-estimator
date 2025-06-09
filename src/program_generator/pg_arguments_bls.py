import csv
import fire
import random
import sys
from py_ecc.bls12_381 import (G1, G2, curve_order, multiply)

WRAPPING_INSTRUCTIONS_COUNT = 5


def get(l, index, default=None):
  return l[index] if -len(l) <= index < len(l) else default

class Program(object):
    """
    POD object for a program
    """

    def __init__(self, bytecode, precompile, op_count, nominal_gas_cost, args):
        self.bytecode = bytecode
        self.precompile = precompile
        self.op_count = op_count
        self.nominal_gas_cost = nominal_gas_cost
        self.arg0 = get(args, 0)
        self.arg1 = get(args, 1)
        self.arg2 = get(args, 2)


class ProgramGenerator(object):
    """
    Sample program generator for EVM instrumentation

    If used with `--fullCsv`, will print out a CSV in the following format:
    ```
    | program_id | precompile | op_count | bytecode |
    ```

    """

    def __init__(self, seed=0):
        random.seed(a=seed, version=2)

    def generate(self, fullCsv=True, count=1, opcode=None, opCount=10):
        """
        Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
        programs to STDOUT

        Parameters:
        fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
        count (int): the number of programs
        opcode (string): if set, will only generate programs for opcode
        opCount (integer): number of measured opcodes, defaults to 10. In total, programs with 0, `opCount` and `2 * opCount` will be generated.

        selectionFile (string): file name of the OPCODE selection file under `data`, defaults to `selection.csv`
        seed: a seed for random number generator, defaults to 0
        """

        programs = self._do_generate(opcode, count, opCount)

        if fullCsv:
            writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

            opcodes = [program.precompile + program.nominal_gas_cost for program in programs]
            op_counts = [program.op_count for program in programs]
            arg0s = [program.arg0 for program in programs]
            arg1s = [program.arg1 for program in programs]
            arg2s = [program.arg2 for program in programs]
            program_ids = [program.precompile + program.nominal_gas_cost + '_' + str(idx) for idx, program in enumerate(programs)]
            bytecodes = [program.bytecode for program in programs]

            header = ['program_id', 'opcode', 'op_count', 'arg0', 'arg1', 'arg2', 'bytecode']
            writer.writerow(header)

            rows = zip(program_ids, opcodes, op_counts, arg0s, arg1s, arg2s, bytecodes)
            for row in rows:
                writer.writerow(row)
        else:
            for program in programs:
                print(program.bytecode)

    def _do_generate(self, opcode, count, op_count):
        op_counts = [0, op_count, op_count * 2]
        programs: list[Program] = []
        if opcode is None or opcode == 'BLS12_PAIRING_CHECK':
            for _ in range(0, count):
                programs.extend(_generate_bls12_pairing_check_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'BLS12_G1MSM':
            for _ in range(0, count):
                programs.extend(_generate_bls12_g1msm_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'BLS12_G2MSM':
            for _ in range(0, count):
                programs.extend(_generate_bls12_g2msm_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'BLS12_G1MSM_S':
            for _ in range(0, count):
                programs.extend(_generate_bls12_g1msm_s_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'BLS12_G2MSM_S':
            for _ in range(0, count):
                programs.extend(_generate_bls12_g2msm_s_programs(op_counts, op_count * 2))
        return programs


def _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code, args):
    """
    Generic program generator
    """

    programs = []
    single_op_pushes = '60ff' * WRAPPING_INSTRUCTIONS_COUNT
    single_op_pops = '50' * WRAPPING_INSTRUCTIONS_COUNT
    noop_args_pops = '61ffff9150'  # instead of pops, replace the target address to 0xffff, setup_code does not put arguments for noop calls on the stack
    args_pops = '50' * 6  # drop the arguments from the stack

    for op_count in op_counts:
        # There should always be additional noop at start, even when creating variant for max_op_count
        noop_calls = '858585858585fa50' * (max_op_count - op_count + 1)
        calls = '858585858585fa50' * op_count

        bytecode = single_op_pushes + setup_code + calls + noop_args_pops + noop_calls + args_pops + single_op_pops
        programs.append(Program(bytecode, precompile, op_count, nominal_gas_cost, args))
    return programs

def random_scalar():
    scalar = random.randrange(1, curve_order - 1)
    encoded_scalar = hex(scalar)[2:].zfill(64)
    return encoded_scalar

def _random_g1():
    scalar = random.randrange(1, curve_order - 1)
    pt = multiply(G1, scalar)
    x, y = pt
    encoded_x = hex(x.n)[2:].zfill(128)  # 64 bytes
    encoded_y = hex(y.n)[2:].zfill(128)  # 64 bytes
    return encoded_x + encoded_y


def _random_g2():
    scalar = random.randrange(1, curve_order - 1)
    pt = multiply(G2, scalar)
    x, y = pt
    x0, x1 = x.coeffs
    y0, y1 = y.coeffs
    encoded_x0 = hex(x0.n)[2:].zfill(128)
    encoded_x1 = hex(x1.n)[2:].zfill(128)
    encoded_y0 = hex(y0.n)[2:].zfill(128)
    encoded_y1 = hex(y1.n)[2:].zfill(128)
    return encoded_x0 + encoded_x1 + encoded_y0 + encoded_y1

def _push2(value):
    encoded_value = hex(value)[2:].zfill(4)
    return '61' + encoded_value

def _fill_input_data_memory(start, data):
    code = ''
    data_pos = 0
    memory_pos = start
    while data_pos < len(data):
        code = code + '7f' + data[data_pos: data_pos + 64] + _push2(memory_pos) + '52'
        data_pos = data_pos + 64
        memory_pos = memory_pos + 32
    return code


def _generate_bls12_pairing_check_programs(op_counts, max_op_count):
    precompile = 'BLS12_PAIRING_CHECK'
    k = random.randint(1, 32)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g1() + _random_g2()

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(k * 384) + '52' + \
        '610020' + \
        _push2(k * 384) + \
        _push2(k * 384) + \
        '6000' + \
        '600f' + \
        '63ffffffff'

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g1msm_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM'
    k = random.randint(1, 128)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g1() + random_scalar()

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(k * 160 + 96) + '52' + \
        '610080' + \
        _push2(k * 160) + \
        _push2(k * 160) + \
        '6000' + \
        '600c' + \
        '63ffffffff'

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g2msm_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM'
    k = random.randint(1, 128)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g2() + random_scalar()

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(k * 288 + 224) + '52' + \
        '610100' + \
        _push2(k * 288) + \
        _push2(k * 288) + \
        '6000' + \
        '600e' + \
        '63ffffffff'

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g1msm_s_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM_S'
    k = random.randint(1, 8)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g1() + random_scalar()

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(k * 160 + 96) + '52' + \
        '610080' + \
        _push2(k * 160) + \
        _push2(k * 160) + \
        '6000' + \
        '600c' + \
        '63ffffffff'

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g2msm_s_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM_S'
    k = random.randint(1, 8)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g2() + random_scalar()

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(k * 288 + 224) + '52' + \
        '610100' + \
        _push2(k * 288) + \
        _push2(k * 288) + \
        '6000' + \
        '600e' + \
        '63ffffffff'

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def main():
    fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
    main()
