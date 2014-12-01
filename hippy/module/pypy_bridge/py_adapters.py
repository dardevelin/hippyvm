"""
The data structures defined here all wrap Python objects in some way so
that they can be used in PHP programs.
"""

from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import def_class, W_InvokeCall
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root, W_Object as WPh_Object
from hippy.function import AbstractFunction
from hippy.objects.iterator import BaseIterator
from hippy.objects.arrayobject import wrap_array_key, W_ArrayObject
from hippy.objects.reference import W_Reference
from hippy.builtin_klass import W_ExceptionObject, k_Exception

from pypy.interpreter.argument import Arguments
from pypy.interpreter.error import OperationError
from pypy.interpreter.pycode import PyCode
from pypy.interpreter.function import Function as PyFunction
from pypy.objspace.std.listobject import W_ListObject as WPy_ListObject

from rpython.rlib import jit


class W_PyGenericAdapter(W_InstanceObject):
    """Generic adapter for Python objects in PHP.
    Used if no specific adapter exists"""

    _immutable_fields_ = ["interp", "w_py_inst"]

    def setup_instance(self, interp, w_py_inst):
        self.interp = interp
        self.w_py_inst = w_py_inst

    def get_wrapped_py_obj(self):
        return self.w_py_inst

    # Use this as a low level ctor instead of the above.
    @classmethod
    def from_w_py_inst(cls, interp, w_py_inst):
        w_py_adptr = W_PyGenericAdapter(k_PyGenericAdapter, [])
        w_py_adptr.setup_instance(interp, w_py_inst)
        return w_py_adptr

    def get_callable(self):
        """PHP interpreter calls this when calls a wrapped Python var"""
        return W_EmbeddedPyCallable(self.w_py_inst)

    def to_py(self, interp, w_php_ref=None):
        return self.w_py_inst

    def as_string(self, space, quiet=False):
        """ Tells PHP how to str_w this should we wrap a string """
        return self.w_py_inst.to_php(self.interp)

@wrap_method(['interp', ThisUnwrapper(W_PyGenericAdapter), str],
        name='GenericPyProxy::__get')
def generic__get(interp, this, name):
    interp = this.interp
    py_space = interp.py_space
    w_py_target = py_space.getattr(this.w_py_inst, py_space.wrap(name))
    return w_py_target.to_php(interp)

@wrap_method(['interp', ThisUnwrapper(W_PyGenericAdapter), str, Wph_Root],
        name='GenericPyProxy::__call')
@jit.unroll_safe
def generic__call(interp, this, func_name, w_php_args):
    from hippy.interpreter import Interpreter
    assert isinstance(interp, Interpreter)

    py_space = interp.py_space
    w_py_func_name = py_space.wrap(func_name)
    w_py_func = py_space.getattr(this.w_py_inst, w_py_func_name)

    w_py_args_items = [ x.to_py(interp) for x in w_php_args.as_list_w() ]
    w_py_rv = interp.py_space.call(w_py_func,
            interp.py_space.newlist(w_py_args_items))
    return w_py_rv.to_php(interp)

k_PyGenericAdapter = def_class('PyGenericAdapter',
    [generic__get, generic__call],
    [], instance_class=W_PyGenericAdapter
)

class W_EmbeddedPyCallable(W_InvokeCall):

    _immutable_fields_ = [ "w_py_func" ]

    def __init__(self, w_py_func):
        W_InvokeCall.__init__(self, None, None, None)
        self.w_py_func = w_py_func

    @jit.unroll_safe
    def call_args(self, interp, args_w,
            w_this=None, thisclass=None, closureargs=None):
        py_space = interp.py_space

        w_py_args_elems = [ x.to_py(interp) for x in args_w ]

        try:
            rv = py_space.call_args(
                    self.w_py_func, Arguments(py_space, w_py_args_elems))
        except OperationError as e:
            # Convert the Python exception to a PHP one.
            e.normalize_exception(py_space)
            w_py_exn = e.get_w_value(py_space)
            w_php_exn = w_py_exn.to_php(interp)
            from hippy.error import Throw
            raise Throw(w_php_exn)

        return rv.to_php(interp)

    def needs_ref(self, i):
        w_py_func = self.w_py_func
        if isinstance(w_py_func, PyFunction):
            return i in w_py_func.code.co_php_args_by_ref
        else:
            return False

    def needs_val(self, i):
        w_py_func = self.w_py_func
        if isinstance(w_py_func, PyFunction):
            return not i in w_py_func.code.co_php_args_by_ref
        else:
            return True

    def is_py_call(self):
        return True

class W_PyFuncGlobalAdapter(AbstractFunction):
    _immutable_fields_ = ["interp", "w_py_callable"]

    def __init__(self, interp, w_py_callable):
        from hippy.module.pypy_bridge.php_adapters import W_PHPFuncAdapter
        assert not isinstance(w_py_callable, W_PHPFuncAdapter)

        self.interp = interp
        self.w_py_callable = w_py_callable

    def get_wrapped_py_obj(self):
        return self.py_callable

    @jit.unroll_safe
    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):

        py_space = interp.py_space

        w_py_args_elems = [x.to_py(interp) for x in args_w]

        # Methods are really just functions with self bound
        if w_this is not None:
            w_py_args_elems = [w_this.to_py(interp)] + w_py_args_elems

        w_py_rv = py_space.call_args(self.w_py_callable,
                Arguments(py_space, w_py_args_elems))

        return w_py_rv.to_php(interp)

    def _arg_index_adjust(self, i):
        return i

    def needs_ref(self, i):
        w_py_callable = self.w_py_callable
        if isinstance(w_py_callable, PyFunction):
            i = self._arg_index_adjust(i)
            return i in w_py_callable.code.co_php_args_by_ref
        else:
            return False

    def needs_value(self, i):
        w_py_callable = self.w_py_callable
        if isinstance(w_py_callable, PyFunction):
            i = self._arg_index_adjust(i)
            return not i in w_py_callable.code.co_php_args_by_ref
        else:
            return True

    def is_py_call(self):
        return True

    def get_identifier(self):
        return self.w_py_callable.name.lower()

class W_PyMethodFuncAdapter(W_PyFuncGlobalAdapter):
    """Only exists because method indicies for methods are skewed by one
    between Python and PHP. In PHP $this is implicit"""

    def _arg_index_adjust(self, i):
        return i + 1

class W_PyFuncAdapter(W_InstanceObject):
    """A 'lexically scoped' embedded Python function.
    Essentially these instances behave a bit like a PHP closure."""

    _immutable_fields_ = [ "interp", "w_py_func" ]

    def __init__(self, interp, w_py_func, klass, storage_w):
        from hippy.module.pypy_bridge.php_adapters import W_PHPFuncAdapter
        assert not isinstance(w_py_func, W_PHPFuncAdapter)

        self.interp = interp
        self.w_py_func = w_py_func
        W_InstanceObject.__init__(self, klass, storage_w)

    def setattr(self, interp, attr, w_value, contextclass, unique_item=False):
        interp.catchable_fatal(
                "W_PyFuncAdapter object cannot have properties")

    def setattr_ref(self, interp, attr, w_value, contextclass):
        interp.catchable_fatal(
                "W_PyFuncAdapter object cannot have properties")

    def clone(self, interp, contextclass):
        raise NotImplementedError("Not implemented")

    def get_callable(self):
        return W_EmbeddedPyCallable(self.w_py_func)

    def to_py(self, interp, w_php_ref=None):
        return self.w_py_func

    def get_identifier(self):
        return self.w_py_callable.name.lower()

k_PyFuncAdapter = def_class('PyFunc', [])

def new_embedded_py_func(interp, w_py_func):
    return W_PyFuncAdapter(interp, w_py_func, k_PyFuncAdapter,
            k_PyFuncAdapter.get_initial_storage_w(interp.space)[:])

class W_PyModAdapter(WPh_Object):
    _immutable_fields_ = ["py_space", "w_py_mod"]

    def __init__(self, py_space, w_py_mod):
        self.py_space = py_space
        self.w_py_mod = w_py_mod

    def get_wrapped_py_obj(self):
        return self.w_py_mod

    def _getattr(self, interp, space, name):
        w_py_mod = self.w_py_mod
        py_space = self.py_space
        try:
            w_obj = py_space.getattr(w_py_mod, py_space.wrap(name))
        except OperationError, e:
            if not e.match(py_space, py_space.w_AttributeError):
                raise
            raise space.ec.fatal("No such member %s in module" % name)
        return w_obj.to_php(interp)

    def getmeth(self, space, name, contextclass=None, for_callback=None):
        interp = self.py_space.get_php_interp()
        return self._getattr(interp, space, name)

    def getattr(self, interp, name, contextclass=None,
            give_notice=False, fail_with_none=False):
        return self._getattr(interp, interp.space, name)

    def to_py(self, interp, w_php_ref=None):
        return self.w_py_mod

class W_PyListAdapterIterator(BaseIterator):

    _immutable_fields_ = ["py_space", "storage_w"]

    def __init__(self, py_space, w_py_list):
        self.py_space = py_space
        self.storage_w = py_space.listview(w_py_list)
        self.index = 0
        self.finished = len(self.storage_w) == 0

    def get_wrapped_py_obj(self):
        # Iterators can reasonably be considered opaque from a wrapping
        # perspective.
        return None

    def next(self, space):
        index = self.index
        w_py_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return w_py_value.to_php(self.py_space.get_php_interp())

    def next_item(self, space):
        index = self.index
        w_py_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return space.wrap(index), \
                w_py_value.to_php(self.py_space.get_php_interp())

class W_PyListAdapter(W_ArrayObject):
    """Wraps a Python list as PHP array."""

    _immutable_fields_ = ["py_space", "w_py_list"]

    _has_string_keys = False

    def __init__(self, py_space, w_py_list):
        assert isinstance(w_py_list, WPy_ListObject)
        self.py_space = py_space
        self.w_py_list = w_py_list

    def get_wrapped_py_obj(self):
        return self.w_py_list

    def arraylen(self):
        py_space = self.py_space
        return py_space.int_w(py_space.len(self.w_py_list))

    def copy(self):
        # used for copy on write semantics of PHP
        w_py_list_copy = self.w_py_list.clone()
        return W_PyListAdapter(self.py_space, w_py_list_copy)

    def _getitem_int(self, index):
        py_space = self.py_space
        w_py_val = py_space.getitem(self.w_py_list, py_space.wrap(index))
        return w_py_val.to_php(py_space.get_php_interp())

    def _getitem_str(self, index):
        from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
        _raise_php_bridgeexception(self.py_space.get_php_interp(),
               "Cannot access string keys of wrapped Python list")

    def _appenditem(self, w_obj, as_ref=False):
        self.w_py_list.append(w_obj.to_py(self.py_space.get_php_interp()))

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        w_py_val = w_value.to_py(py_space.get_php_interp())
        w_py_index = py_space.wrap(index)
        py_space.setitem(self.w_py_list, w_py_index, w_py_val)
        return self

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
        _raise_php_bridgeexception(self.py_space.get_php_interp(),
               "Cannot set string keys of wrapped Python list")

    def create_iter(self, space, contextclass=None):
        return W_PyListAdapterIterator(self.py_space, self.w_py_list)

    def to_py(self, interp, w_php_ref=None):
        # array-like structures in PHP are always converted to a dict-like
        # python structure. Here, a list pretending to be a dict.
        from hippy.module.pypy_bridge.py_strategies import (
                make_dict_like_py_list)
        return make_dict_like_py_list(interp, self.w_py_list)

class W_PyDictAdapterIterator(BaseIterator):

    _immutable_fields_ = ["interp", "w_py_iter"]

    def __init__(self, py_space, rdct_w):
        self.py_space = py_space
        self.w_py_iter = rdct_w.iteritems()
        self.remaining = py_space.int_w(py_space.len(rdct_w))
        self.finished = self.remaining == 0

    def get_wrapped_py_obj(self):
        # Iterators can reasonably be considered opaque from a wrapping
        # perspective.
        return None

    def next(self, space):
        py_space = self.py_space
        self.remaining -= 1
        self.finished = self.remaining == 0
        w_py_v = self.w_py_iter.next_item()[1]
        return w_py_v.to_php(py_space.get_php_interp())

    def next_item(self, space):
        py_space = self.py_space
        interp = py_space.get_php_interp()
        self.remaining -= 1
        self.finished = self.remaining == 0
        w_py_k, w_py_v = self.w_py_iter.next_item()
        return w_py_k.to_php(interp), w_py_v.to_php(interp)

    def to_py(self, interp, w_php_ref=None):
        return None

class W_PyDictAdapter(W_ArrayObject):
    """Wraps a Python dict as a PHP array."""

    _immutable_fields_ = ["py_space", "w_py_dict"]

    def __init__(self, py_space, w_py_dict):
        self.py_space = py_space
        self.w_py_dict = w_py_dict

    def copy(self):
        # used for copy on write semantics of PHP
        w_py_dict_copy = self.w_py_dict.descr_copy(self.py_space)
        return W_PyDictAdapter(self.py_space, w_py_dict_copy)

    def get_wrapped_py_obj(self):
        return self.w_py_dict

    def arraylen(self):
        return self.py_space.int_w(self.py_space.len(self.w_py_dict))

    def _getitem_int(self, index):
        py_space = self.py_space
        w_py_val = py_space.getitem(self.w_py_dict, py_space.wrap(index))
        return w_py_val.to_php(py_space.get_php_interp())

    def _getitem_str(self, index):
        py_space = self.py_space
        w_py_val = py_space.getitem(self.w_py_dict, py_space.wrap(index))
        return w_py_val.to_php(py_space.get_php_interp())

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        w_py_val = w_value.to_py(py_space.get_php_interp())
        w_py_index = py_space.wrap(index)
        py_space.setitem(self.w_py_dict, w_py_index, w_py_val)
        return self

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        w_py_val = w_value.to_py(py_space.get_php_interp())
        w_py_key = py_space.wrap(key)
        py_space.setitem(self.w_py_dict, w_py_key, w_py_val)
        return self

    def create_iter(self, space, contextclass=None):
        return W_PyDictAdapterIterator(self.py_space, self.w_py_dict)

    def to_py(self, interp, w_php_ref=None):
        return self.w_py_dict

class W_PyExceptionAdapter(W_ExceptionObject):
    """Wraps up a Python exception"""

    def __init__(self, klass, dct_w):
        W_ExceptionObject.__init__(self, klass, dct_w)
        self.w_py_exn = None

    def set_w_py_exception(self, php_interp, w_py_exn):
        W_ExceptionObject.setup(self, php_interp)
        self.w_py_exn = w_py_exn

        php_space, py_space = php_interp.space, php_interp.py_space

        # XXX these need to be properly populated to give the user a
        # meaningful error message. The comments show how these fields
        # would be populated if they were a standard PHP exception.

        #this.setattr(interp, 'file', space.wrap(this.traceback[0][0]), k_Exception)
        self.file = None

        #this.setattr(interp, 'line', space.wrap(this.traceback[0][2]), k_Exception)
        self.line = -1

        #this.setattr(interp, 'message', space.wrap(message), k_Exception)
        w_py_exn_str = py_space.getattr(self.w_py_exn, py_space.wrap("message"))
        msg = py_space.str_w(w_py_exn_str)
        self.setattr(php_interp, 'message',
                php_space.wrap(msg), k_PyExceptionAdapter)

        #this.setattr(interp, 'code', space.wrap(code), k_Exception)
        self.code = None

@wrap_method(['interp', ThisUnwrapper(W_PyExceptionAdapter)], name='PyException::getMessage')
def w_py_exc_getMessage(interp, this):
    return this.getattr(interp, "message")

k_PyExceptionAdapter = def_class('PyException',
    [w_py_exc_getMessage], [], instance_class=W_PyExceptionAdapter)

from hippy.builtin_klass import k_Exception
# Indicates an error in PHP->Py glue code
k_BridgeException = def_class('BridgeException', [], [], extends=k_Exception)
