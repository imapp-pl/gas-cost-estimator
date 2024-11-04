import os
import csv
import fire
import random
import sys

import constants
from common import generate_single_marginal, prepare_opcodes, get_selection, arity, random_value_byte_size_push, byte_size_push

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

    def generate(self, fullCsv=False, maxOpCount=50, stepOpCount=5):
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
            _generate_sha2_256_programs(op_counts, max_op_count) + \
            _generate_ripemd_160_programs(op_counts, max_op_count) + \
            _generate_identity_programs(op_counts, max_op_count) + \
            _generate_modexp_programs(op_counts, max_op_count) + \
            _generate_ecadd_programs(op_counts, max_op_count) + \
            _generate_ecmul_programs(op_counts, max_op_count) + \
            _generate_ecpairing_programs(op_counts, max_op_count) + \
            _generate_blake2f_programs(op_counts, max_op_count) + \
            _generate_pointeval_programs(op_counts, max_op_count)
        return programs


def _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code):
    """
    Generic program generator
    """
    programs = []
    single_op_pushes = '60ff' * WRAPPING_INSTRUCTIONS_COUNT
    single_op_pops = '50' * WRAPPING_INSTRUCTIONS_COUNT

    for op_count in op_counts:
        calls = '858585858585fa50' * op_count
        no_ops = '85858585858550' * (max_op_count - op_count)

        bytecode = single_op_pushes + setup_code + calls + no_ops + single_op_pops
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


def _generate_sha2_256_programs(op_counts, max_op_count):
    precompile = 'SHA2-256'
    setup_code = '60ff60005260ff6020526020602060206000600263ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_ripemd_160_programs(op_counts, max_op_count):
    precompile = 'RIPEMD-160'
    setup_code = '60ff60005260ff6020526020602060206000600363ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_identity_programs(op_counts, max_op_count):
    precompile = 'IDENTITY'
    setup_code = '60ff60005260fa6020526020602060206000600463ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_modexp_programs(op_counts, max_op_count):
    precompile = 'MODEXP'
    setup_code = '6004600052600160205260046040527fabcdef1108abcdef22000000000000000000000000000000000000000000000060605260ff6080526004609c60806000600563ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_ecadd_programs(op_counts, max_op_count):
    precompile = 'ECADD'
    setup_code = '600160005260026020526001604052600260605260ff60805260ff60a0526040608060806000600663ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_ecmul_programs(op_counts, max_op_count):
    precompile = 'ECMUL'
    setup_code = '60016000526002602052600260405260ff60605260ff6080526040606060606000600763ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_ecpairing_programs(op_counts, max_op_count):
    precompile = 'ECPAIRING'

    programs = []

    nominal_gas_cost = '79000'
    setup_code = (
        '7f089142debb13c461f61523586a60732d8b69c5b38a3380a74da7b2961d867dbf600052'
        '7f2d5fc7bbc013c16d7945f190b232eacc25da675c0eb093fe6b9f1b4b4e107b36602052'
        '7f29f2c1dbcc614745f242077001ec9edd475acdab9ab435770d456bd22bbd2abf604052'
        '7f268683f9b1be0bde4508e2e25e51f6b44da3546e87524337d506fd03c4ff7ce0606052'
        '7f1851abe58ef4e08916bec8034ca62c04cd08340ab6cc525e6170634092622165608052'
        '7f1b71422869c92e49465200ca19033a8aa425f955be3d8329c4475503e45c00e160a052'
        '60ff60c052602060c060c06000600863ffffffff'
    )
    programs += _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code)

    nominal_gas_cost = '113000'
    setup_code = (
        '7f2cf44499d5d27bb186308b7af7af02ac5bc9eeb6a3d147c186b21fb1b76e18da600052'
        '7f2c0f001f52110ccfe69108924926e45f0b0c868df0e7bde1fe16d3242dc715f6602052'
        '7f1fb19bb476f6b9e44e2a32234da8212f61cd63919354bc06aef31e3cfaff3ebc604052'
        '7f22606845ff186793914e03e21df544c34ffe2f2f3504de8a79d9159eca2d98d9606052'
        '7f2bd368e28381e8eccb5fa81fc26cf3f048eea9abfdd85d7ed3ab3698d63e4f90608052'
        '7f2fe02e47887507adf0ff1743cbac6ba291e66f59be6bd763950bb16041a0a85e60a052'
        '7f000000000000000000000000000000000000000000000000000000000000000160c052'
        '7f30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd4560e052'
        '7f1971ff0471b09fa93caaf13cbf443c1aede09cc4328f5a62aad45f40ec133eb461010052'
        '7f091058a3141822985733cbdddfed0fd8d6c104e9e9eff40bf5abfef9ab163bc761012052'
        '7f2a23af9a5ce2ba2796c1f4e453a370eb0af8c212d9dc9acd8fc02c2e907baea261014052'
        '7f23a8eb0b0996252cb548a4487da97b02422ebc0e834613f954de6c7e0afdc1fc61016052'
        '60ff6101805260206101806101806000600863ffffffff'
    )
    programs += _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code)

    nominal_gas_cost = '181000'
    setup_code = (
        '7f03d310db98253bb4a3aaff90eeb790d236cbc5698d5a9a6014965acff56e759a61000052'
        '7f1edc5e9ae29193d6e5deed5c3ac4171cae2da155880cf6058848318de6859ea261002052'
        '7f1ee564b4d91e10d3c3a34787dc163a79bf9d571eeb67ff072609cbe19ff25fc761004052'
        '7f270e094c2467dcf6ecf8c97a09ef643cfff359cbec1426c5eb01864b5cf3c27361006052'
        '7f09f432f65daced7c895c3748fa0b0dfc430584e419442a25b98e74400789801261008052'
        '7f10fa7bc208e286ebea1f5c342a96782b563a0bc4cdb4c42ba151b9cb76eea93d6100a052'
        '7f0abcdaf6ffdf0cbf20235077c7bb3908b74b9a8252083f4b01dcbe84cab90fc76100c052'
        '7f1a9681988a15b7eea9ae8cb0c2210b870eec2366e0531c414abb65c668c6eb3e6100e052'
        '7f21d0be81c5698882ee63cb729ed3f5b725d7a670b76941ddffff9ddca50cf9af61010052'
        '7f21e61a0ac51a17c0128baa2cda8f212b13943959cf26a7578342c93dd2de7deb61012052'
        '7f194e408b546197d9ee99d643e5385dcb8d5904854d8a836763ab8ce20f9b502761014052'
        '7f222aced81c808247572971b490eef1515a49f651f7df254de2b35310bb5b78c261016052'
        '7f18b2345c40036ea331bfcfb8536739a5e5530027709adae6632a3613cd0838cd61018052'
        '7f204121beebd54ec6bb063ba5a6d84eeceda2a733260066c90d332425e992ef6c6101a052'
        '7f2b0f794d64952d560a422a7ff549a58bfaa0cf791ab6dfad1c4941e1907804036101c052'
        '7f24bad1c848f2d8efcd716f7d814c46e2632e74a5b8d455a64c55917b220aab986101e052'
        '7f2ed4bbed5f80fac726f4a95789fee7905eef0a241596acbea4268ec3f2b87f3161020052'
        '7f29563b69a30c11a856f68c72f129988e8636c86f57467cba299cdb4917469b4961022052'
        '7f137a989e5d714b4b882d4a455600940ab63b14f23e7934ddd62cf5181099c63b61024052'
        '7f2f57525eb3d19451024a4e71ee09c72c5b7e0dff925001acaee126bcd29db5f661026052'
        '7f00d8ff46230e348d08dcbcdb1f85a5a43aa7b4f51841f1d4f98c18bbb576519861028052'
        '7f2cabdf6326194120727367bdae0b081aa7da12c8f8c6af0ce27d2f8d0f059fe16102a052'
        '7f240c9c5a6993d344744d77bbb855960b6704e91846cf362444bff1ccaf45a7c26102c052'
        '7f17873a5d7834d0c1d7d9bab5f9934d7ac218834aa916d459d8ceafc280d59efb6102e052'
        '60ff6103005260206103006103006000600863ffffffff'
    )
    programs += _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code)

    nominal_gas_cost = '317000'
    setup_code = (
        '7f03d333c171b569f9721355f4b5f9569c18006d55ea805d0ab72f392e6e6be88e61000052'
        '7f230688a302d20e6934bc1151bf8a0af65d4294568f5af0b041197aaec74aabea61002052'
        '7f1aae25b6edb4994684b2877875575b74c14a19eb068d429accd0bbbcd4de1d1161004052'
        '7f0b2f112b63197fcaa10a2afb08cd221bd509c829efecdd4a3bade00bf947cc3961006052'
        '7f11796bc946a8148ce73aa901e2e1f4dcb259b11ee880e088ddff65f5f6f05d4461008052'
        '7f1ae8c9a28a7ee1d483dc47235e16e19303455ee1b7c6c29fdff01d3eab2c4e776100a052'
        '7f284e25e7b8203b7b40dbf1bfcdb4fbdedea474fd44ed67dab27a031959453e9b6100c052'
        '7f0010adb1d55c492437f0bab7e1b63a56467681f06a29aca6ab95d29d5fd23c356100e052'
        '7f29e107847478c3dd0aeb69d6c4345dd0239ba105a1bddc699512e027bbb34b8161010052'
        '7f111903892d003d32111610c7ccd4c529f75cc8bf33a894f40756510ec8b9bcfd61012052'
        '7f0402b66e82c6b8fd6de9652d5c81821f69445b0dca7cd052e1811760803f778a61014052'
        '7f1ae8318c37a3652bdcab122282e95dd3f7393b3214e8ce290c01c9345ce81d1c61016052'
        '7f09304eb9899baa26aa963503f8a55ed2a5d0cc2d5d0fbdfae81c3a823790d23761018052'
        '7f1874cf1b2e447a896844c5338098f2ad9dea545e40d5f5a4369125d95fcd5acf6101a052'
        '7f0c0ffafa0ba1c1053fdc155d63329f5d8540fe5c6a876793e04913a1e6a7c8886101c052'
        '7f15fe284d364a500612c376e7bd39a466e1b9c4c0a85b105d15a973db33a0f1d46101e052'
        '7f2ee64373074312ec2147daed5fbc660ff99664dcb993750af8f192ee51b849a561020052'
        '7f1d9a24c4dbe4f69715d00e8ede2f32c2a54c5e8f8a57487cf80dad49915cdc1861022052'
        '7f239b7847b2fe9c17f926ad11e5161802872b6607265d5bf10c737d9eb157506c61024052'
        '7f05725034e5c2a941efb693478b4401e684afba8af20cfc14c53f66652c737ab761026052'
        '7f1657a4156fc5dc9ddf2b07d05c72395c7bb98f97743c6a81dcc11d25dcf3138961028052'
        '7f0effb8dceb430ae9009afe11d1f00e0ec2ca627ce9c4919287a319590dfba56d6102a052'
        '7f1d76f3288b570588497d0e5cc88341ba9b40b8fee65f042836161d718ebba1226102c052'
        '7f03bab8927db4e4b4dcf9ca7f4250c61d0a055985996d04e0c76d49bc83bad37e6102e052'
        '7f0a1a1f642a16d95eaddfb9b7a403bdd032f07c9222813df4dda4aa3054716d7661030052'
        '7f22a999ac90eaa7bbc4ec78bb5d47736aaf04f706ddcc4724776a5dc0bc39cd1a61032052'
        '7f0c9c5fb89113f93dc81db66c1ca13534f16518fb0347056c08bac62a1bcd1b2061034052'
        '7f1516a4f52fca78d9d140d40687b093176eb90fb236c03cad3ebf57027afc117461036052'
        '7f2095f3a98a957815f7b13e263a5f11bccea9f6e716e219915e9075d9c0c2a8e061038052'
        '7f260e553a1182aa35b5d8d710c9705010e1350c02b6a217ec61245bee22c850986103a052'
        '7f10027b242574ec29b652f249774d7320612dde5ca36f20f42bb169352a568e4c6103c052'
        '7f14a972b4ef4a1ca49f0e4b095f77ec5929486d1a051ed3b766a40d442e8e7d3b6103e052'
        '7f04ebc527aedcdd807d94774c23dbf3bf2841a2a0e3272e10431a056b1fb1224d61040052'
        '7f16565b2f5350a0c8bcdcc6a3a2d189cc488c6c88cf9a0bd213248f73095f4ac061042052'
        '7f116d2a932043b527cb2a7c42e329a00310c9418da803179a099418ddb9ed859b61044052'
        '7f06035b9b8fa5ebdbcc460641e8af2bd20e68e62d50563672a52294cc0e94cb3361046052'
        '7f1287c3cc9c9b8f389de88ed033ca26234d38089a712dfac171b8c8d743c5a25661048052'
        '7f0b1f5c5d64fb31d6830a6c982fc8daafcc6b2ac02ac20685e11cf211edadf2bc6104a052'
        '7f01f9b7d3b716110dbfcda9974d00a0e90721e9aae490f3e0ba84b55cefa949196104c052'
        '7f197ef9a4b21ccef5186f0d9801a25cbb77227b2d8488fa8da35e8c70495fb6866104e052'
        '7f1997575cfbbc644daf21868564be6a9fbfd216b252271f08fce405355d84d49061050052'
        '7f28f6c5397686e765c5157034c2ed2f92e2d11c7411613f5c60b5ee50540df6fc61052052'
        '7f025a3e1aee7b30e3113afca04fa7e3949a54f65a25aa8241d5056f289c3378a761054052'
        '7f2d4730731a6659294dfe163718d63cc6239d09033ba48004c52a9d55d66317b661056052'
        '7f2493908d3215efe3d2cb77ff6447a971599b2df711a59395515c4cac93a0f22161058052'
        '7f1fada2e1799efd65247699ffbc3b35cce7d210a61e868d3bd8abb37e20bd5afe6105a052'
        '7f2a628ffe54a17a274af70c3584b4f9a2e567c6ae5d5a00d14ac7ffc12d04e06a6105c052'
        '7f03d1fee23fa99c63fb8a760fe4794af4221f7bb7ceb194c7df2c63859c8b03296105e052'
        '60ff6106005260206106006106006000600863ffffffff'
    )
    programs += _generate_programs(op_counts, max_op_count, precompile, nominal_gas_cost, setup_code)

    return programs


def _generate_blake2f_programs(op_counts, max_op_count):
    precompile = 'BLAKE2F'
    setup_code = \
        '630000000c6003537f48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af5' + \
        '4fa56004527fd182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b60' + \
        '24527f616263000000000000000000000000000000000000000000000000000000000060445260' + \
        '0360c453600160d45360ff60e05260ff61010052604060e060d56000600963ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)


def _generate_pointeval_programs(op_counts, max_op_count):
    precompile = 'POINTEVAL'
    setup_code = \
        '7f013c03613f6fc558fb7e61e75602241ed9a2f04e36d8670aadd286e71b5ca9cc610' + \
        '000527f42000000000000000000000000000000000000000000000000000000000000' + \
        '00610020527f31e5a2356cbc2ef6a733eae8d54bf48719ae3d990017ca787c419c7d3' + \
        '69f8e3c610040527f83fac17c3f237fc51f90e2c660eb202a438bc2025baded5cd193' + \
        'c1a018c5885b610060527fc9281ba704d5566082e851235c7be763b2a99adff965e0a' + \
        '121ee972ebc472d02610080527f944a74f5c6243e14052e105124b70bf65faf85ad3a' + \
        '494325e269fad097842cba6100a05260ff6100c05260ff6100e052604060c060c0600' + \
        '0600a63ffffffff'
    return _generate_programs(op_counts, max_op_count, precompile, '', setup_code)

def main():
    fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
    main()
