import csv
import fire
import random
import sys


WRAPPING_INSTRUCTIONS_COUNT = 5


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
            _generate_bls12_g1msm_k0_programs(op_counts, max_op_count) + \
            _generate_bls12_g1msm_k1_programs(op_counts, max_op_count) + \
            _generate_bls12_g1msm_k2_programs(op_counts, max_op_count) + \
            _generate_bls12_g2msm_k0_programs(op_counts, max_op_count) + \
            _generate_bls12_g2msm_k1_programs(op_counts, max_op_count) + \
            _generate_bls12_g2msm_k2_programs(op_counts, max_op_count) + \
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
        calls = '858585858585fa50' * op_count

        bytecode = single_op_pushes + setup_code + calls + noop_args_pops + noop_calls + args_pops + single_op_pops
        programs.append(Program(bytecode, precompile, op_count, nominal_gas_cost))
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


def _generate_bls12_g1add_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1ADD'
    setup_code = (
        '7f00000000000000000000000000000000112b98340eee2777cc3c14163dea3ec9'
        '61000052'
        '7f7977ac3dc5c70da32e6e87578f44912e902ccef9efe28d4a78b8999dfbca9426'
        '61002052'
        '7f00000000000000000000000000000000186b28d92356c4dfec4b5201ad099dbd'
        '61004052'
        '7fede3781f8998ddf929b4cd7756192185ca7b8f4ef7088f813270ac3d48868a21'
        '61006052'
        '7f00000000000000000000000000000000002c8bc5f39b2c9fea01372429e92a9c'
        '61008052'
        '7f945fad152da67174f4e478fdead734d50f6e2da867c235f1f2f11bdfee67d2a7'
        '6100a052'
        '7f000000000000000000000000000000000c1dd27aad9f5d48c4824da3071daedf'
        '6100c052'
        '7f0c7a0e2a0b0ed39c50c9d25e61334a9c96765e049542ccaa00e0eccb316eec08'
        '6100e052'
        '60ff61016052'
        '6080'
        '610100'
        '610100'
        '6000'
        '600b'
        '63ffffffff'
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_g2add_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2ADD'
    setup_code = (
        '7f00000000000000000000000000000000103121a2ceaae586d240843a39896732'
        '61000052'
        '7f5f8eb5a93e8fea99b62b9f88d8556c80dd726a4b30e84a36eeabaf3592937f27'
        '61002052'
        '7f00000000000000000000000000000000086b990f3da2aeac0a36143b7d7c8244'
        '61004052'
        '7f28215140db1bb859338764cb58458f081d92664f9053b50b3fbd2e4723121b68'
        '61006052'
        '7f000000000000000000000000000000000f9e7ba9a86a8f7624aa2b42dcc8772e'
        '61008052'
        '7f1af4ae115685e60abc2c9b90242167acef3d0be4050bf935eed7c3b6fc7ba77e'
        '6100a052'
        '7f000000000000000000000000000000000d22c3652d0dc6f0fc9316e14268477c'
        '6100c052'
        '7f2049ef772e852108d269d9c38dba1d4802e8dae479818184c08f9a569d878451'
        '6100e052'
        '7f000000000000000000000000000000000bcd916c5888735aa593466e6ab908a0'
        '61010052'
        '7f5af528f34a7901fb60feb1f51737c73612436c192dfdecf927019724ab2a9b79'
        '61012052'
        '7f00000000000000000000000000000000187d4ccf6c22381d0c40c9d7820ff8ef'
        '61014052'
        '7fe6298c6dad0caa25402412661737cb482dba2719c3a50ec08cd022230952dfc6'
        '61016052'
        '7f00000000000000000000000000000000164510d4f2cf1e14e039561f1baf82be'
        '61018052'
        '7fa678d0065e378d5bb7443fa782e6ab2a3bf7e4ea125d6415a8277c60f5346468'
        '6101a052'
        '7f000000000000000000000000000000000281f2e28b73eca4db9966456b75de9a'
        '6101c052'
        '7fe3830c74ac928fc4c36b4aeaaffd47ee587d948f68056df2826ca2775415a53a'
        '6101e052'
        '60ff6102e052'
        '610100'
        '610200'
        '610200'
        '6000'
        '600d'
        '63ffffffff'
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_g1msm_setup_code():
    setup_code = (
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
        '61xxxx'
        '6000'
        '600c'
        '63yyyyyyyy'
    )
    return setup_code

def _generate_bls12_g1msm_k2_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM_K2'
    setup_code = _generate_bls12_g1msm_setup_code()
    setup_code = setup_code.replace('xxxx', '0140').replace('yyyyyyyy', 'ffffffff')
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_bls12_g1msm_k1_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM_K1'
    setup_code = _generate_bls12_g1msm_setup_code()
    setup_code = setup_code.replace('xxxx', '00a0').replace('yyyyyyyy', 'ffffffff')
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_g1msm_k0_programs(op_counts, max_op_count):
    precompile = 'BLS12_G1MSM_K0'
    setup_code = _generate_bls12_g1msm_setup_code()
    setup_code = setup_code.replace('xxxx', '009f').replace('yyyyyyyy', '00000400')
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_g2msm_setup_code():
    setup_code = (
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
        '61xxxx'
        '6000'
        '600e'
        '63yyyyyyyy'
    )
    return setup_code

def _generate_bls12_g2msm_k2_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM_K2'
    setup_code = _generate_bls12_g2msm_setup_code()
    setup_code = setup_code.replace('xxxx', '0240').replace('yyyyyyyy', 'ffffffff')
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_g2msm_k1_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM_K1'
    setup_code = _generate_bls12_g2msm_setup_code()
    setup_code = setup_code.replace('xxxx', '0120').replace('yyyyyyyy', 'ffffffff')
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_g2msm_k0_programs(op_counts, max_op_count):
    precompile = 'BLS12_G2MSM_K0'
    setup_code = _generate_bls12_g2msm_setup_code()
    setup_code = setup_code.replace('xxxx', '011f').replace('yyyyyyyy', '00000400')
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_pairing_check_programs(op_counts, max_op_count):
    precompile = 'BLS12_PAIRING_CHECK'
    setup_code = (
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
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_map_fp_to_g1_programs(op_counts, max_op_count):
    precompile = 'BLS12_MAP_FP_TO_G1'
    setup_code = (
        '7f0000000000000000000000000000000008dccd088ca55b8bfbc96fb50bb25c59'
        '61000052'
        '7f2faa867a8bb78d4e94a8cc2c92306190244532e91feba2b7fed977e3c3bb5a1f'
        '61002052'
        '60ff6100a052'
        '610080'
        '610040'
        '610040'
        '6000'
        '6010'
        '63ffffffff'
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def _generate_bls12_map_fp_to_g2_programs(op_counts, max_op_count):
    precompile = 'BLS12_MAP_FP_TO_G2'
    setup_code = (
        '7f0000000000000000000000000000000018c16fe362b7dbdfa102e42bdfd3e2f4'
        '61000052'
        '7fe6191d479437a59db4eb716986bf08ee1f42634db66bde97d6c16bbfd342b3b8'
        '61002052'
        '7f000000000000000000000000000000000e37812ce1b146d998d5f92bdd5ada2a'
        '61004052'
        '7f31bfd63dfe18311aa91637b5f279dd045763166aa1615e46a50d8d8f475f184e'
        '61006052'
        '60ff61016052'
        '610100'
        '610080'
        '610080'
        '6000'
        '6011'
        '63ffffffff'
    )
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def main():
    fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
    main()
