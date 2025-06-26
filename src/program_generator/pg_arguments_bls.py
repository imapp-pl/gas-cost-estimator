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
    input_data = input_data + ('00' * 384 * (32-k))

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(32 * 384) + '52' + \
        '610020' + \
        _push2(k * 384) + \
        _push2(k * 384) + \
        '6000' + \
        '600f' + \
        '63ffffffff'
    setup_code = BLS12_PAIRING_CHECK_WARMUP + setup_code

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g1msm_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM'
    k = random.randint(1, 128)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g1() + random_scalar()
    input_data = input_data + ('00' * 160 * (128-k))

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(128 * 160 + 96) + '52' + \
        '610080' + \
        _push2(k * 160) + \
        _push2(k * 160) + \
        '6000' + \
        '600c' + \
        '63ffffffff'
    setup_code = BLS12_G1MSM_WARMUP + setup_code

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g2msm_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM'
    k = random.randint(1, 128)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g2() + random_scalar()
    input_data = input_data + ('00' * 288 * (128-k))

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(128 * 288 + 224) + '52' + \
        '610100' + \
        _push2(k * 288) + \
        _push2(k * 288) + \
        '6000' + \
        '600e' + \
        '63ffffffff'
    setup_code = BLS12_G2MSM_WARMUP + setup_code

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g1msm_s_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM_S'
    k = random.randint(1, 8)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g1() + random_scalar()
    input_data = input_data + ('00' * 160 * (8-k))

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(8 * 160 + 96) + '52' + \
        '610080' + \
        _push2(k * 160) + \
        _push2(k * 160) + \
        '6000' + \
        '600c' + \
        '63ffffffff'
    setup_code = BLS12_G1MSM_WARMUP + setup_code

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


def _generate_bls12_g2msm_s_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM_S'
    k = random.randint(1, 8)
    input_data = ''
    for _ in range(0, k):
        input_data = input_data + _random_g2() + random_scalar()
    input_data = input_data + ('00' * 288 * (8-k))

    setup_code = _fill_input_data_memory(0, input_data)
    setup_code = setup_code + \
        '60ff' + _push2(8 * 288 + 224) + '52' + \
        '610100' + \
        _push2(k * 288) + \
        _push2(k * 288) + \
        '6000' + \
        '600e' + \
        '63ffffffff'
    setup_code = BLS12_G2MSM_WARMUP + setup_code

    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code, [k])


BLS12_PAIRING_CHECK_WARMUP = (
    '7f000000000000000000000000000000000491d1b0ecd9bb917989f0e74f0dea04'
    '61000052'
    '7f22eac4a873e5e2644f368dffb9a6e20fd6e10c1b77654d067c0618f6e5a7f79a'
    '61002052'
    '7f0000000000000000000000000000000017cd7061575d3e8034fcea62adaa1a3b'
    '61004052'
    '7fc38dca4b50e4c5c01d04dd78037c9cee914e17944ea99e7ad84278e5d49f36c4'
    '61006052'
    '7f000000000000000000000000000000000bc2357c6782bbb6a078d9e171fc7a81'
    '61008052'
    '7ff7bd8ca73eb485e76317359908bb09bd372fd362a637512a9d48019b383e5489'
    '6100a052'
    '7f0000000000000000000000000000000004b8f49c3bac0247a09487049492b0ed'
    '6100c052'
    '7f99cf90c56263141daa35f011330d3ced3f3ad78d252c51a3bb42fc7d8f182594'
    '6100e052'
    '7f000000000000000000000000000000000982d17b17404ac198a0ff5f2dffa56a'
    '61010052'
    '7f328d95ec4732d9cca9da420ec7cf716dc63d56d0f5179a8b1ec71fe0328fe882'
    '61012052'
    '7f00000000000000000000000000000000147c92cb19e43943bb20c5360a6c4347'
    '61014052'
    '7f411eb8ffb3d6f19cc428a8dc0cb3fd1eb3ad02b1c21e21c78f65a7691ee63de9'
    '61016052'
    '7f0000000000000000000000000000000016cae74dc6523e5273dbd2d9d25c53f1'
    '61018052'
    '7fe2c453e6d9ba3f605021cfb514fa0bdf721b05f2200f32591d733e739fabf438'
    '6101a052'
    '7f000000000000000000000000000000001405df65fb71b738510b3a2fc31c33ef'
    '6101c052'
    '7f3d884ccc84efb1017341a368bf40727b7ad8cdc8e3fd6b0eb94102488c5cb770'
    '6101e052'
    '7f00000000000000000000000000000000024aa2b2f08f0a91260805272dc51051'
    '61020052'
    '7fc6e47ad4fa403b02b4510b647ae3d1770bac0326a805bbefd48056c8c121bdb8'
    '61022052'
    '7f0000000000000000000000000000000013e02b6052719f607dacd3a088274f65'
    '61024052'
    '7f596bd0d09920b61ab5da61bbdc7f5049334cf11213945d57e5ac7d055d042b7e'
    '61026052'
    '7f000000000000000000000000000000000d1b3cc2c7027888be51d9ef691d77bc'
    '61028052'
    '7fb679afda66c73f17f9ee3837a55024f78c71363275a75d75d86bab79f74782aa'
    '6102a052'
    '7f0000000000000000000000000000000013fa4d4a0ad8b1ce186ed5061789213d'
    '6102c052'
    '7f993923066dddaf1040bc3ff59f825c78df74f2d75467e25e0f55f8a00fa030ed'
    '6102e052'
    '60ff61030052'
    '610020'
    '610300'
    '610300'
    '6000'
    '600f'
    '63ffffffff'
    'fa50'
)

BLS12_G1MSM_WARMUP = (
    '7f000000000000000000000000000000000bc83829ec8e98081abac2fa8e0572e8'
    '61000052'
    '7f19b570b2499d4cd1e6748f48c350c392f5d52c672dd0bbcdf1469414d7ce929c'
    '61002052'
    '7f00000000000000000000000000000000007d1574eb65b391475b49857766c808'
    '61004052'
    '7ffa95ac2a78755d8d740d2df90bfa9aab3dd5c850d536c9794f6cfa2f004b4550'
    '61006052'
    '7fc067ecd54e9ef59996493f846ecca63bbd7ec28da586f0b8d41bfdc6d97a35cb'
    '61008052'
    '7f00000000000000000000000000000000022e4ed74f98d69a9bb1037a307eed57'
    '6100a052'
    '7f210d3ca92648ca9c54546c7b57102558ab12f5d2bb46502ba3c07529f64b72b3'
    '6100c052'
    '7f0000000000000000000000000000000005ea660c44a9d36696a899ed1bbef1d9'
    '6100e052'
    '7f51656f2eae553f4f124ac9cee3d7de13556a7884ffc07e20d5afb7bdb9c6f163'
    '61010052'
    '7f8b5112baca5e0f2bfb885c5041189612918d203a117d886bcb3b27df7e64d17d'
    '61012052'
    '60ff6101a052'
    '610080'
    '610140'
    '610140'
    '6000'
    '600c'
    '63ffffffff'
    'fa50'
)

BLS12_G2MSM_WARMUP = (
    '7f00000000000000000000000000000000039b10ccd664da6f273ea134bb55ee48'
    '61000052'
    '7ff09ba585a7e2bb95b5aec610631ac49810d5d616f67ba0147e6d1be476ea220e'
    '61002052'
    '7f0000000000000000000000000000000000fbcdff4e48e07d1f73ec42fe7eb026'
    '61004052'
    '7ff5c30407cfd2f22bbbfe5b2a09e8a7bb4884178cb6afd1c95f80e646929d3004'
    '61006052'
    '7f0000000000000000000000000000000001ed3b0e71acb0adbf44643374edbf44'
    '61008052'
    '7f05af87cfc0507db7e8978889c6c3afbe9754d1182e98ac3060d64994d31ef576'
    '6100a052'
    '7f000000000000000000000000000000001681a2bf65b83be5a2ca50430949b6e2'
    '6100c052'
    '7fa099977482e9405b593f34d2ed877a3f0d1bddc37d0cec4d59d7df74b2b8f2df'
    '6100e052'
    '7fb3c940fe79b6966489b527955de7599194a9ac69a6ff58b8d99e7b1084f0464e'
    '61010052'
    '7f0000000000000000000000000000000018c0ada6351b70661f053365deae5691'
    '61012052'
    '7f0798bd2ace6e2bf6ba4192d1a229967f6af6ca1c9a8a11ebc0a232344ee0f6d6'
    '61014052'
    '7f000000000000000000000000000000000cc70a587f4652039d8117b6103858ad'
    '61016052'
    '7fcd9728f6aebe230578389a62da0042b7623b1c0436734f463cfdd187d2090324'
    '61018052'
    '7f0000000000000000000000000000000009f50bd7beedb23328818f9ffdafdb6d'
    '6101a052'
    '7fa6a4dd80c5a9048ab8b154df3cad938ccede829f1156f769d9e149791e8e0cd9'
    '6101c052'
    '7f00000000000000000000000000000000079ba50d2511631b20b6d6f3841e616e'
    '6101e052'
    '7f9d11b68ec3368cd60129d9d4787ab56c4e9145a38927e51c9cd6271d493d9388'
    '61020052'
    '7f4d0e25bf3f6fc9f4da25d21fdc71773f1947b7a8a775b8177f7eca990b05b71d'
    '61022052'
    '60ff61032052'
    '610100'
    '610240'
    '610240'
    '6000'
    '600e'
    '63ffffffff'
    'fa50'
)


def main():
    fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
    main()
