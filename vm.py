import dis
import inspect
import opcode
import sys
import operator
import types
from functools import partial
from time import sleep
# import six

from utils import run_vm


class Frame(object):
    def __init__(self, bytecode, back_frame=None, global_names=None,
                 local_names=None):
        self.bytecode = bytecode
        self.back_frame = back_frame
        self.global_names = global_names if global_names is not None else {}
        self.global_names.update({'__builtins__': __builtins__})
        self.local_names = local_names if local_names is not None else {}
        self.local_names.update({'__builtins__': __builtins__})
        self.command_id = 0
        self.commands = list(dis.get_instructions(bytecode))
        if back_frame:
            self.builtins_names = back_frame.builtins_names
        else:
            self.builtins_names = __builtins__.__dict__


# вызов функции тестирующего фреймворка
class VirtualMachine(object):
    def __init__(self):
        self.frames = []
        self.running_frame_id = -1
        self.functions = {
            "LOAD_NAME": self._load_name,
            "DELETE_NAME": self._delete_name,
            "LOAD_CONST": self._load_const,
            "CALL_FUNCTION": self._call_function,
            "CALL_FUNCTION_EX": self._call_function_ex,
            "CALL_FUNCTION_KW": self._call_function_kw,
            "POP_TOP": self._pop_top,
            "RETURN_VALUE": self._return_value,
            "STORE_NAME": self._store_name,
            "LOAD_ATTR": self._load_attr,
            "STORE_ATTR": self._store_attr,
            "DELETE_ATTR": self._delete_attr,

            "STORE_SUBSCR": self._store_subscr,
            "DELETE_SUBSCR": self._delete_subscr,
            # TODO тест на это
            "PRINT_EXPR": self._print_expr,
            "UNPACK_SEQUENCE": self._unpack_sequence,
            "UNPACK_EX": self._unpack_ex,

            # бинарные операции
            "BINARY_ADD": partial(self._bin_op, operator=operator.add),
            "BINARY_POWER": partial(self._bin_op, operator=operator.pow),
            "BINARY_MULTIPLY": partial(self._bin_op, operator=operator.mul),
            "BINARY_MATRIX_MULTIPLY":
                partial(self._bin_op, operator=operator.matmul),
            "BINARY_FLOOR_DIVIDE":
                partial(self._bin_op, operator=operator.floordiv),
            "BINARY_TRUE_DIVIDE":
                partial(self._bin_op, operator=operator.truediv),
            "BINARY_MODULO": partial(self._bin_op, operator=operator.mod),
            "BINARY_SUBTRACT": partial(self._bin_op, operator=operator.sub),
            "BINARY_SUBSCR": partial(self._bin_op, operator=operator.getitem),
            "BINARY_LSHIFT": partial(self._bin_op, operator=operator.lshift),
            "BINARY_RSHIFT": partial(self._bin_op, operator=operator.rshift),
            "BINARY_AND": partial(self._bin_op, operator=operator.and_),
            "BINARY_XOR": partial(self._bin_op, operator=operator.xor),
            "BINARY_OR": partial(self._bin_op, operator=operator.or_),

            # inplace бинарные
            "INPLACE_ADD": partial(self._bin_op, operator=operator.iadd),
            "INPLACE_POWER": partial(self._bin_op, operator=operator.ipow),
            "INPLACE_MULTIPLY": partial(self._bin_op, operator=operator.imul),
            "INPLACE_MATRIX_MULTIPLY":
                partial(self._bin_op, operator=operator.imatmul),
            "INPLACE_FLOOR_DIVIDE":
                partial(self._bin_op, operator=operator.ifloordiv),
            "INPLACE_TRUE_DIVIDE":
                partial(self._bin_op, operator=operator.itruediv),
            "INPLACE_MODULO": partial(self._bin_op, operator=operator.imod),
            "INPLACE_SUBTRACT": partial(self._bin_op, operator=operator.isub),
            "INPLACE_LSHIFT": partial(self._bin_op, operator=operator.ilshift),
            "INPLACE_RSHIFT": partial(self._bin_op, operator=operator.irshift),
            "INPLACE_AND": partial(self._bin_op, operator=operator.iand),
            "INPLACE_XOR": partial(self._bin_op, operator=operator.ixor),
            "INPLACE_OR": partial(self._bin_op, operator=operator.ior),

            # унарные операции
            "UNARY_POSITIVE": partial(self._unary_op, operator=operator.pos),
            "UNARY_NEGATIVE": partial(self._unary_op, operator=operator.neg),
            "UNARY_NOT": partial(self._unary_op, operator=operator.not_),
            "UNARY_CONVERT": partial(self._unary_op, operator=repr),
            "UNARY_INVERT": partial(self._unary_op, operator=operator.invert),

            'COMPARE_OP': self._compare_op,

            'POP_JUMP_IF_FALSE': self._pop_jump_if_false,
            'POP_JUMP_IF_TRUE': self._pop_jump_if_true,
            'JUMP_ABSOLUTE': self._jump_absolute,
            'JUMP_FORWARD': self._jump_forward,
            'JUMP_IF_FALSE_OR_POP': self._jump_if_false_or_pop,
            'JUMP_IF_TRUE_OR_POP': self._jump_if_true_or_pop,
            'SETUP_LOOP': self._setup_loop,
            'BREAK_LOOP': self._break_loop,
            'CONTINUE_LOOP': self._continue_loop,
            'GET_ITER': self._get_iter,
            'FOR_ITER': self._for_iter,
            'POP_BLOCK': self._pop_block,
            'BUILD_LIST': self._build_list,
            # TODO тест на это
            'LIST_APPEND': self._list_append,
            'BUILD_SET': self._build_set,
            # TODO тест на это
            'SET_ADD': self._set_add,
            # TODO тест на это
            'BUILD_TUPLE': self._build_tuple,
            'BUILD_CONST_KEY_MAP': self._built_const_key_map,
            'BUILD_MAP': self._build_map,
            # TODO тест на это
            'MAP_ADD': self._map_add,
            # TODO тест на это
            'BUILD_STRING': self._build_string,
            'BUILD_SLICE': self._build_slice,

            'ROT_TWO': self._rot_two,
            'ROT_THREE': self._rot_three,
            'DUP_TOP': self._dup_top,
            'DUP_TOP_TWO': self._dup_top_two,

            'MAKE_FUNCTION': self._make_function,
            'LOAD_FAST': self._load_fast,
            'STORE_FAST': self._store_fast,
            'DELETE_FAST': self._delete_fast,
            # TODO понять в чем разница между LOAD_GLOBAL и LOAD_NAME
            'LOAD_GLOBAL': self._load_name,
            'NOP': self._nop,

            'LOAD_BUILD_CLASS': self._load_build_class,
            'SETUP_EXCEPT': self._setup_exept,
            'RAISE_VARARGS': self._raise_varargs,

        }
        self.stack = []
        self.block_stack = []
        self.return_value = None

    def _make_frame(self, code, args={}, global_names=None,
                    local_names=None):
        if global_names is not None:
            if local_names is None:
                local_names = global_names
        local_names.update(args)
        global_names = self.frames[-1].global_names
        return Frame(code, self.frames[-1], global_names, local_names)

    def run_code(self, bytecode):
        """
            :type: code_obj
        """

        if type(bytecode) is str:
            bytecode = compile(''.join(bytecode), '<test>', 'exec')
        self.running_frame_id = 0
        self.return_value = None
        self._run_frame(Frame(bytecode))

    def _run(self):
        """
        зупустить верхний фрейм
        вернуть его результат
        """
        return self._run_frame(self.frames[0])

    def _run_frame(self, frame):
        self.frames.append(frame)
        self.running_frame_id = len(self.frames) - 1
        self.frames[-1].command_id = 0
        while self.frames[-1].command_id < len(self.frames[-1].commands):
            command = self.frames[-1].commands[self.frames[-1].command_id]
            self.frames[-1].command_id += 1
            self.functions[command.opname](command)
        self.frames.pop()
        self.running_frame_id -= 1
        return self.return_value

    def _load_name(self, command):
        """
        положить на вершину стека функцию описанную в command
        """
        function_name = command.argval
        working_frame = self.frames[self.running_frame_id]
        if function_name in working_frame.local_names:
            self.stack.append(working_frame.local_names[function_name])
        elif function_name in working_frame.global_names:
            self.stack.append(working_frame.global_names[function_name])
        elif function_name in working_frame.builtins_names:
            self.stack.append(working_frame.builtins_names[function_name])
        else:
            raise NameError("not found {}".format(function_name))

    def _delete_name(self, command):
        function_name = command.argval
        working_frame = self.frames[self.running_frame_id]
        if function_name in working_frame.local_names:
            del working_frame.local_names[command.argval]
        elif function_name in working_frame.global_names:
            del working_frame.global_names[command.argval]
        elif function_name in working_frame.builtins_names:
            del working_frame.builtins_names[command.argval]
        else:
            raise NameError("not found {}".format(function_name))

    def _load_const(self, command):
        """
        положить на вершину стека константу описанную в command
        """
        self.stack.append(command.argval)

    def _call_function(self, command, args=[]):
        """
        снять со стека аргументы функции и функцию,
        запустить функцию с аргументами,
        положить результат выполнения обратно на стек
        """
        # получим количество именнованных и неименованных аргументов
        named_len, pos_len = divmod(command.argval, 256)
        # print(command)
        self._build_map(command, named_len)
        named_params = self.stack.pop()
        self._build_list(command, pos_len)
        params = self.stack.pop()
        params.extend(args)
        func_name = self.stack.pop()
        # print(func_name)
        # print(params)
        if func_name == __build_class__:
            self.stack.append(__build_class__(*params, **named_params))
        else:
            self.stack.append(func_name(*params, **named_params))

    def _call_function_ex(self, command):
        """
        взять имя функции с вершины стека,
        дальше взять позиционные аргементы и именнованные аргументы
        """
        kwargs = None
        if command.argval != 0:
            kwargs = self.stack.pop()
        args = self.stack.pop()
        func_name = self.stack.pop()
        if kwargs is not None:
            self.stack.append(func_name(*args, **kwargs))
        else:
            self.stack.append(func_name(*args))

    def _call_function_kw(self, command):
        self._call_function(command, self.stack.pop())

    def _pop_top(self, command):
        """
        снять со стека верхний элемент
        """
        self.stack.pop()

    def _return_value(self, command):
        """
        вернет вершину стека в качестве возвращаемого значения,
        уберет элемент в вершины стека
        """
        self.return_value = self.stack.pop()
        return self.return_value

    def _store_name(self, command):
        """
        проассоциирует локально имя из command со значением на вершине стека
        """
        self.frames[self.running_frame_id].local_names[command.argval] = (
            self.stack.pop()
        )

    def _load_attr(self, command):
        """
        заменит элемент на вершине стека его аттрибутом
        """
        top_of_stack = self.stack.pop()
        self.stack.append(getattr(top_of_stack, command.argval))

    def _store_attr(self, command):
        first = self.stack.pop()
        second = self.stack.pop()
        setattr(first, command.argval, second)
        self.stack.append(first)

    def _delete_attr(self, command):
        first = self.stack.pop()
        delattr(first, command.argval)
        self.stack.append(first)

    def _store_subscr(self, command):
        first = self.stack.pop()
        second = self.stack.pop()
        third = self.stack.pop()
        second[first] = third
        self.stack.append(second)

    def _delete_subscr(self, command):
        first = self.stack.pop()
        second = self.stack.pop()
        del second[first]
        self.stack.append(second)

    def _print_expr(self, command):
        print(self.stack.pop())

    def _unpack_sequence(self, command):
        """
        разложить верхний элемент стека
        """
        sequence = list(self.stack.pop())
        sequence.reverse()
        for x in sequence:
            self.stack.append(x)

    def _unpack_ex(self, command):
        # узнаем есть ли такое в тестах
        # sleep(100000)
        assert False

    def _bin_op(self, command, operator=None):
        """
        реализация всех бинарных операторов
        взять со стека два аргумента и пременить к ним оператор,
        результат положить на стек
        """
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(operator(left, right))

    def _unary_op(self, command, operator=None):
        """
        реализация всех унарных операторов
        взять со стека элемент применить к нему operand
        положить результат на стек
        """
        value = self.stack.pop()
        self.stack.append(operator(value))

    compare_functions = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
        "is": lambda a, b: a is b,
        "is not": lambda a, b: a is not b,
        # "is instance": lambda a, b: a isinstance(b),
    }

    def _compare_op(self, command):
        """
        реализация всех возможных операций сравнения и принадлежности
        берет два аргумента со стека, положит на стек возвращаемое значение
        """
        self._bin_op(command, self.compare_functions[command.argval])

    def _pop_jump_if_false(self, command):
        """
        jump вперед если не выполнено условие на вершине стека
        """
        tos_value = self.stack.pop()
        if not tos_value:
            self._jump_absolute(command)

    def _pop_jump_if_true(self, command):
        """
        jump вперед если выполнено условие на вершине стека
        """
        tos_value = self.stack.pop()
        if tos_value:
            self._jump_absolute(command)

    def _jump_forward(self, command):
        """
        безусловный Jump вперед
        """
        while self.frames[-1].commands[self.frames[-1].command_id].offset < \
                command.argval:
            self.frames[-1].command_id += 1

    def _jump_if_true_or_pop(self, command):
        """
        jump если на вершине стека true, иначе убрать значение с вершины стека
        """
        tos_value = self.stack[-1]
        if tos_value:
            self._jump_forward(command)
        else:
            self.stack.pop()

    def _jump_if_false_or_pop(self, command):
        """
        jump если на вершине стека false, иначе убрать значение с вершины стека
        """
        tos_value = self.stack[-1]
        if not tos_value:
            self._jump_forward(command)
        else:
            self.stack.pop()

    def _setup_loop(self, command):
        """
        положить на вершину стека блоков новый цикл
        """
        self.block_stack.append(Block("loop", command.argval))

    def _break_loop(self, command):
        if self.block_stack[-1].type != "loop":
            # способ увидеть ошибку на сервере
            assert False
            sleep(1000000)
        self._jump_absolute(command, self.block_stack[-1].offset)

    def _continue_loop(self, command):
        self._jump_absolute(command)

    def _get_iter(self, command):
        """
        применить iter к верхушке стека
        """
        self.stack[-1] = iter(self.stack[-1])

    def _for_iter(self, command):
        """
        попробовать применить next к макушке стека, если не получится,
        то прыгнуть на delta вперед
        """
        try:
            self.stack.append(next(self.stack[-1]))
        except StopIteration:
            self.stack.pop()
            self._jump_forward(command)

    def _jump_absolute(self, command, needTo=None):
        """
        продвинутся по командам до указанной позиции
        """
        if needTo is None:
            needTo = command.argval
        while self.frames[-1].commands[self.frames[-1].command_id].offset \
                > needTo:
            self.frames[-1].command_id -= 1
        while self.frames[-1].commands[self.frames[-1].command_id].offset \
                < needTo:
            self.frames[-1].command_id += 1

    def _pop_block(self, command):
        """
        убрать верхний элемент с блокового стека
        """
        self.block_stack.pop()

    def _build_list(self, command, argval=None):
        """
        убрать с вершины стека command.argval элементов,
        сделать из них лист и положить обратно
        """
        len_of_list = command.argval
        if argval is not None:
            len_of_list = argval
        result_list = []
        for i in range(len_of_list):
            result_list.append(self.stack[-1])
            self.stack.pop()
        result_list.reverse()
        self.stack.append(result_list)

    def _list_append(self, command):
        first = self.stack.pop()
        second = self.stack.pop()
        list.append(second[-command.argval], first)
        self.stack.append(second)

    def _build_set(self, command):
        """
        собрать сет по элементам с вершины стека
        """
        self._build_list(command)
        built_set = set(self.stack.pop())
        self.stack.append(built_set)

    def _set_add(self, command):
        first = self.stack.pop()
        second = self.stack.pop()
        set.add(second[-command.argval], first)
        self.stack.append(second)

    def _build_tuple(self, command):
        """
        собрать tuple по элементам с вершины стека
        """
        self._build_list(command)
        built_set = tuple(self.stack.pop())
        self.stack.append(built_set)

    def _built_const_key_map(self, command):
        """
        собрать мап из элементов. ключи лежат в tuple сверху стека
        дальше в стеке по одному лежат значения по ключу
        """
        built_dict = {}
        keys = list(self.stack.pop())
        self._build_list(command)
        values = self.stack.pop()
        for i in range(command.argval):
            key = keys[i]
            value = values[i]
            built_dict[key] = value
        self.stack.append(built_dict)

    def _build_map(self, command, argval=None):
        """
        собрать мап из элементов. в стеке поочереди лежат ключи и значения
        """
        built_dict = {}
        keys = []
        values = []
        len_of_dict = command.argval
        if argval is not None:
            len_of_dict = argval
        for i in range(len_of_dict):
            values.append(self.stack.pop())
            keys.append(self.stack.pop())

        keys.reverse()
        values.reverse()
        for i in range(len_of_dict):
            key = keys[i]
            value = values[i]
            built_dict[key] = value
        self.stack.append(built_dict)

    def _map_add(self, command):
        first = self.stack.pop()
        second = self.stack.pop()
        dict.setitem(second[-command.argval], first, second)
        self.stack.append(second)

    def _build_string(self, command):
        """
        собрать строку с макушки стека
        """
        self._build_list(command)
        string_value = ''.join(self.stack.pop())
        self.stack.append(string_value)

    def _build_slice(self, command):
        args = [self.stack.pop(), self.stack.pop()]
        if command.argval == 3:
            args.append(self.stack.pop())
        args.reverse()
        self.stack.append(slice(*args))

    def _rot_two(self, command):
        """
        похоже поменять местами два верхних элемента стека
        """
        left = self.stack.pop()
        right = self.stack.pop()
        self.stack.append(left)
        self.stack.append(right)

    def _rot_three(self, command):
        """
        опустить вехний элемент стека на две позиции
        """
        first = self.stack.pop()
        second = self.stack.pop()
        third = self.stack.pop()
        self.stack.append(first)
        self.stack.append(third)
        self.stack.append(second)

    def _dup_top(self, command):
        self.stack.append(self.stack[-1])

    def _dup_top_two(self, command):
        # TODO прочекать что это работает верно
        self.stack.append(self.stack[-2])
        self.stack.append(self.stack[-2])

    def _make_function(self, command):
        func_name = self.stack.pop()
        code_object = self.stack.pop()
        default_args = ()
        if command.argval > 0:
            default_args = self.stack.pop()
        # new_func = Function(func_name, code_object, default_args,
        #                     self.frames[self.running_frame_id].global_names,
        #                     self)
        new_func = \
            types.FunctionType(code_object,
                               self.frames[
                                   self.running_frame_id].global_names,
                               func_name,
                               default_args,
                               None
                               )
        self.stack.append(new_func)

    def _load_fast(self, command):
        if command.argval in self.frames[-1].local_names:
            self.stack.append(self.frames[-1].local_names[command.argval])

    def _store_fast(self, command):
        self.frames[-1].local_names[command.argval] = self.stack.pop()

    def _delete_fast(self, command):
        del self.frames[-1].local_names[command.argval]

    # def _load_global(self, command):
    #     frame = self.frames[-1]
    #     name = command.argval
    #     value = None
    #     if name in frame.global_names:
    #         self.stack.append(frame.global_names[name])
    #     elif name in frame.local_names:
    #         self.stack.append(frame.local_names[name])
    #     else:
    #         assert False

    def _nop(self, command):
        return

    def _load_build_class(self, command):
        self.stack.append(__build_class__)

    def _setup_exept(self, command):
        self.block_stack.append(Block("exeption", command.argval))

    # TODO доделать обработку исключений
    def _raise_varargs(self, command):
        # print(command)
        # print(self.stack)
        cause = exc = None
        if command.argval == 2:
            cause = self.stack.pop()
            exc = self.stack.pop()
            raise exc
            # six.reraise(type(exc), exc, cause)
        elif command.argval == 1:
            exc = self.stack.pop()
            raise exc
            # six.reraise(type(exc), exc)


class Function(object):
    def __init__(self, name, code, default_args, names_global, vm):
        self.name = name
        self.code = code
        self.names_global = names_global
        self.vm = vm
        self.default_args = tuple(default_args)
        kw = {'argdefs': self.default_args}
        self.func = types.FunctionType(code, names_global, **kw)

    def __call__(self, *args, **kwargs):
        # сопоставить имена аргументов в словарь
        callargs = inspect.getcallargs(self.func, *args, **kwargs)
        # print(callargs)
        frame = self.vm._make_frame(self.code, callargs, self.names_global, {})
        return self.vm._run_frame(frame)


class Block(object):
    def __init__(self, type, offset):
        self.type = type
        self.offset = offset

if __name__ == "__main__":
    vm = VirtualMachine()
    run_vm(vm)
