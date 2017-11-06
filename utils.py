import dis
import subprocess
from contextlib import redirect_stdout
from contextlib import redirect_stderr
import sys

from io import StringIO

# количество запускаемых тест кейсов
num_cases = 50

def print_delimeter():
    print("_" * 80)


def run_vm(virtual_machine):
    print("test started...\n")
    for i in range(num_cases):
        test_file = str(i) + ".py"
        print("Run test {}".format(test_file))
        with open(test_file) as file_with_test:
            code = file_with_test.readlines()
            print(code)
            compiled_code = compile(''.join(code), '<test>', 'exec')
            dis.dis(compiled_code)
            print_delimeter()
            print("true res = ", end='')
            trueErrors = StringIO()
            trueResult = StringIO()
            #sys.stderr = trueErrors
                with redirect_stdout(trueResult):
                code_t = ''.join(code)
                exec(code_t)
            print(trueResult.getvalue())
            print("vm res = ", end='')
            vmErrors = StringIO()
            #sys.stderr = vmErrors
            vmResult = StringIO()
            with redirect_stdout(vmResult):
                virtual_machine.run_code(compiled_code)
            # virtual_machine.run_code(compiled_code)
            print(vmResult.getvalue() + "\n")
            print("errors" + vmErrors.getvalue())
            assert(vmResult.getvalue() == trueResult.getvalue())
            assert(vmErrors.getvalue() == trueErrors.getvalue())