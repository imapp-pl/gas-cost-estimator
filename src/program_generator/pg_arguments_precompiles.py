import csv
import fire
import random
import sys

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
        if opcode is None or opcode == 'SHA2-256':
            # _generate_ecrecover_programs(op_counts, max_op_count) + \
            for _ in range(0, count):
                programs.extend(_generate_sha2_256_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'RIPEMD-160':
            for _ in range(0, count):
                programs.extend(_generate_ripemd_160_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'IDENTITY':
            for _ in range(0, count):
                programs.extend(_generate_identity_programs(op_counts, op_count * 2))
        if opcode is None or opcode == 'MODEXP':
            for _ in range(0, count):
                programs.extend(_generate_modexp_programs(op_counts, op_count * 2))
        return programs


def _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code, args):
    """
    Generic program generator
    """

    programs = []
    single_op_pushes = '60ff' * WRAPPING_INSTRUCTIONS_COUNT
    single_op_pops = '50' * WRAPPING_INSTRUCTIONS_COUNT
    noop_args_pops = '505050505050'  # 6xPOP

    for op_count in op_counts:
        # There should always be additional noop at start, even when creating variant for max_op_count
        noop_calls = '858585858585fa50' * (max_op_count - op_count + 1)
        calls = '858585858585fa50' * op_count

        bytecode = single_op_pushes + setup_code + noop_calls + noop_args_pops + calls + single_op_pops
        programs.append(Program(bytecode, precompile, op_count, nominal_gas_cost, args))
    return programs


def _generate_ecrecover_programs(op_counts, max_op_count):
    precompile = 'ECRECOVER'
    setup_code = (
        '7f456e9aea5e197a1f1af7a3e85a3212fa4049a3ba34c2289b4c860fc0b0c64ef'
        '3600052601c6020527f9242685bf161793cc25603c231bc2f568eb630ea16aa137d2664ac8038825608'
        '6040527f4f8ae3bd7535248d0bd448298cc2e2071e56992d0774dc340c368ae950852ada60605260ff6'
        '080526020608060806000600163ffffffff'
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_sha2_256_programs(op_counts, max_op_count):
    precompile = 'SHA2-256'
    args = [random.randint(0, (1 << 14) - 1) for _ in range(0, 2)]
    args_pushes = '61%0.4X61%0.4X' % (args[1], args[0]) # reversed order
    setup_code = '6000617fff53' # initial_mem_allocation
    setup_code = setup_code + '5f5f' + args_pushes + '600263ffffffff' # op_call
    setup_code = setup_code + '5f5f' + args_pushes + '61ffff63ffffffff' # noop_call (ffff address)
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, args)


def _generate_ripemd_160_programs(op_counts, max_op_count):
    precompile = 'RIPEMD-160'
    args = [random.randint(0, (1 << 14) - 1) for _ in range(0, 2)]
    args_pushes = '61%0.4X61%0.4X' % (args[1], args[0]) # reversed order
    setup_code = '6000617fff53' # initial_mem_allocation
    setup_code = setup_code + '5f5f' + args_pushes + '600363ffffffff' # op_call
    setup_code = setup_code + '5f5f' + args_pushes + '61ffff63ffffffff' # noop_call (ffff address)
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, args)


def _generate_identity_programs(op_counts, max_op_count):
    precompile = 'IDENTITY'
    args = [random.randint(0, (1 << 14) - 1) for _ in range(0, 2)]
    args_pushes = '61%0.4X61%0.4X' % (args[1], args[0]) # reversed order
    setup_code = '6000617fff53' # initial_mem_allocation
    setup_code = setup_code + '5f5f' + args_pushes + '600463ffffffff' # op_call
    setup_code = setup_code + '5f5f' + args_pushes + '61ffff63ffffffff' # noop_call (ffff address)
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, args)


def _generate_modexp_programs(op_counts, max_op_count):
    precompile = 'MODEXP'
    arg_sizes = [random.randint(1, 32) for _ in range(0, 3)]  # base, exponent, modulo in bytes
    args = [ random.getrandbits(8 * arg_size) for arg_size in arg_sizes]
    print(args)
    setup_code = '600060ff53' # initial_mem_allocation
    # first we put args, because we use MSTORE for potentially less than 32 bytes
    setup_code = setup_code + ('7f%0.64X' % (args[2])) + ('61%0.4X' % (96 + arg_sizes[0] + arg_sizes[1] + arg_sizes[2] - 32)) + '52' # put modulo to mem
    setup_code = setup_code + ('7f%0.64X' % (args[1])) + ('61%0.4X' % (96 + arg_sizes[0] + arg_sizes[1] - 32)) + '52' # put exponent to mem
    setup_code = setup_code + ('7f%0.64X' % (args[1])) + ('61%0.4X' % (96 + arg_sizes[0] - 32)) + '52' # put base to mem
    setup_code = setup_code + ('61%0.4X' % (arg_sizes[0] * 8)) + '6000' + '52' # put base size to mem
    setup_code = setup_code + ('61%0.4X' % (arg_sizes[1] * 8)) + '6020' + '52' # put exponent size to mem
    setup_code = setup_code + ('61%0.4X' % (arg_sizes[2] * 8)) + '6040' + '52' # put modulo size to mem
    params_pushes = '61%0.4X6000' % (96 + arg_sizes[0] + arg_sizes[1] + arg_sizes[2]) # reversed order
    setup_code = setup_code + '5f5f' + params_pushes + '600563ffffffff' # op_call
    setup_code = setup_code + '5f5f' + params_pushes + '61ffff63ffffffff' # noop_call (ffff address)
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, arg_sizes)


def main():
    fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
    main()
