import csv
import fire
import random
import sys
import json


WRAPPING_INSTRUCTIONS_COUNT = 5
TESTS_DIR = 'program_generator/data/'


class Program(object):
    """
    POD object for a program
    """

    def __init__(self, bytecode, precompile, op_count, nominal_gas_cost):
        self.bytecode = bytecode
        self.precompile = precompile
        self.op_count = op_count
        self.nominal_gas_cost = nominal_gas_cost


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

    def generate(self, fullCsv=True, maxOpCount=50, stepOpCount=5):
        """
        Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
        programs to STDOUT

        Parameters:
        fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
        maxOpCount (integer): maximum number of measured opcodes, defaults to 50
        stepOpCount (integer): by how much the number of measured opcodes should increase, defaults to 5
        """

        programs = self._do_generate(maxOpCount, stepOpCount)

        if fullCsv:
            writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

            opcodes = [program.precompile + program.nominal_gas_cost for program in programs]
            op_counts = [program.op_count for program in programs]
            program_ids = [program.precompile + program.nominal_gas_cost +
                           '_' + str(program.op_count) for program in programs]
            bytecodes = [program.bytecode for program in programs]

            header = ['program_id', 'opcode', 'op_count', 'bytecode']
            writer.writerow(header)

            rows = zip(program_ids, opcodes, op_counts, bytecodes)
            for row in rows:
                writer.writerow(row)
        else:
            for program in programs:
                print(program.bytecode)

    def _do_generate(self, max_op_count, step_op_count):
        op_counts = list(range(0, max_op_count + 1, step_op_count))
        programs: list[Program] = \
            _generate_ecrecover_programs(op_counts, max_op_count) + \
            _generate_bls12_g1add_programs(op_counts, max_op_count) + \
            _generate_bls12_g2add_programs(op_counts, max_op_count) + \
            _generate_bls12_g1msm_programs(op_counts, max_op_count) + \
            _generate_bls12_g2msm_programs(op_counts, max_op_count) + \
            _generate_bls12_pairing_check_programs(op_counts, max_op_count) + \
            _generate_bls12_map_fp_to_g1_programs(op_counts, max_op_count) + \
            _generate_bls12_map_fp_to_g2_programs(op_counts, max_op_count)
        return programs


def _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code):
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
        calls = '858585858585fa50' * (op_count + 1)

        bytecode = single_op_pushes + setup_code + calls + noop_args_pops + noop_calls + args_pops + single_op_pops
        programs.append(Program(bytecode, precompile, op_count, nominal_gas_cost))
    return programs


def _generate_ecrecover_programs(op_counts, max_op_count):
    precompile = 'ECRECOVER_TESTS'
    setup_code = (
        '7f456e9aea5e197a1f1af7a3e85a3212fa4049a3ba34c2289b4c860fc0b0c64ef'
        '3600052601c6020527f9242685bf161793cc25603c231bc2f568eb630ea16aa137d2664ac8038825608'
        '6040527f4f8ae3bd7535248d0bd448298cc2e2071e56992d0774dc340c368ae950852ada60605260ff6'
        '080526020608060806000600163ffffffff'
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _push2(value):
    encoded_value = hex(value)[2:].zfill(4)
    return '61' + encoded_value

def _fill_input_data_memory(start, data):
    code = ''
    data_pos = 0
    memory_pos = start
    while data_pos < len(data):
        data_strip = f'{data[data_pos: data_pos + 64]:<064s}'
        code = code + '7f' + data_strip + _push2(memory_pos) + '52'
        data_pos = data_pos + 64
        memory_pos = memory_pos + 32
    return code

def _generate_from_json(op_counts, max_op_count, test, precompile, address, expected_output_bytes_len):
    input_data = test['Input']

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(len(input_data) // 2 + expected_output_bytes_len - 32) + '52' + \
        f'61{expected_output_bytes_len:04x}' + \
        _push2(len(input_data) // 2) + \
        _push2(len(input_data) // 2) + \
        '6000' + \
        '60' + address + \
        '63002fffff'

    return _generate_programs(op_counts, max_op_count, precompile, '_' + test['Name'], setup_code)


def _generate_bls12_g1add_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1ADD'
    address = '0b'
    programs = []
    with open(TESTS_DIR + 'eip-2537/add_G1_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',' + str(test['Gas']) + ',1,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    with open(TESTS_DIR + 'eip-2537/fail-add_G1_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',375,2,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    return programs

def _generate_bls12_g2add_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2ADD'
    address = '0d'
    programs = []
    with open(TESTS_DIR + 'eip-2537/add_G2_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',' + str(test['Gas']) + ',3,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 256)
    with open(TESTS_DIR + 'eip-2537/fail-add_G2_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',600,4,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 256)
    return programs

def _generate_bls12_g1msm_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM'
    address = '0c'
    programs = []
    with open(TESTS_DIR + 'eip-2537/msm_G1_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        if 'discount_table' not in test['Name']:
            # print(precompile + '_' + test['Name'] + ',' + str(test['Gas']) + ',5,0')
            programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    with open(TESTS_DIR + 'eip-2537/fail-msm_G1_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',12000,6,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    return programs

def _generate_bls12_g2msm_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM'
    address = '0e'
    programs = []
    with open(TESTS_DIR + 'eip-2537/msm_G2_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        if 'discount_table' not in test['Name']:
            # print(precompile + '_' + test['Name'] + ',' + str(test['Gas']) + ',7,0')
            programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 256)
    with open(TESTS_DIR + 'eip-2537/fail-msm_G2_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',22500,8,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 256)
    return programs

def _generate_bls12_pairing_check_programs(op_counts, max_op_count):
    precompile = 'BLS12_PAIRING_CHECK'
    address = '0f'
    programs = []
    with open(TESTS_DIR + 'eip-2537/pairing_check_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print('"' + precompile + '_' + test['Name'] + '",' + str(test['Gas']) + ',9,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 32)
    with open(TESTS_DIR + 'eip-2537/fail-pairing_check_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print('"' + precompile + '_' + test['Name'] + '",70300,10,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 32)
    return programs

def _generate_bls12_map_fp_to_g1_programs(op_counts, max_op_count):
    precompile = 'BLS12_MAP_FP_TO_G1'
    address = '10'
    programs = []
    with open(TESTS_DIR + 'eip-2537/map_fp_to_G1_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',' + str(test['Gas']) + ',11,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    with open(TESTS_DIR + 'eip-2537/fail-map_fp_to_G1_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',5500,12,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    return programs

def _generate_bls12_map_fp_to_g2_programs(op_counts, max_op_count):
    precompile = 'BLS12_MAP_FP_TO_G2'
    address = '11'
    programs = []
    with open(TESTS_DIR + 'eip-2537/map_fp2_to_G2_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',' + str(test['Gas']) + ',13,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    with open(TESTS_DIR + 'eip-2537/fail-map_fp2_to_G2_bls.json') as f:
        tests = json.load(f)
    for test in tests:
        # print(precompile + '_' + test['Name'] + ',23800,14,0')
        programs = programs + _generate_from_json(op_counts, max_op_count, test, precompile, address, 128)
    return programs


def main():
    fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
    main()
