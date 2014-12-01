from testing.test_interpreter import MockInterpreter, BaseTestInterpreter

import pytest

class TestPyPyBridgeArrayConversions(BaseTestInterpreter):

    @pytest.fixture
    def php_space(self):
        return self.space

    def test_return_py_list_len_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return [1,2,3]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo(count($ar));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_return_py_list_vals_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return [3, 2, 1]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        for i in range(3):
            assert php_space.int_w(output[i]) == 3 - i

    def test_cannot_getitem_str_on_py_list_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(): return [3, 2, 1]";
            $f = embed_py_func($src);

            $ar = $f();
            try {
                $ar["k"];
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Cannot access string keys of wrapped Python list"
        assert php_space.str_w(output[0]) == err_s

    def test_cannot_setitem_str_on_py_list_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(): return [3, 2, 1]";
            $f = embed_py_func($src);

            $ar = $f();
            try {
                $ar["k"] = "oops";
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Cannot set string keys of wrapped Python list"
        assert php_space.str_w(output[0]) == err_s

    def test_iter_vals_py_list_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return [3, 2, 1]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $i) {
                echo($i);
            }
        ''')
        for i in range(3):
            assert php_space.int_w(output[i]) == 3 - i

    def test_iter_keys_vals_py_list_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $k => $v) {
                echo("$k:$v");
            }
        ''')
        assert php_space.str_w(output[0]) == "0:zero"
        assert php_space.str_w(output[1]) == "1:one"
        assert php_space.str_w(output[2]) == "2:two"


    def test_py_list_setitem_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[1] = "three";
            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert php_space.str_w(output[0]) == "zero"
        assert php_space.str_w(output[1]) == "three"
        assert php_space.str_w(output[2]) == "two"

    def test_py_list_is_copy_on_write_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar1[0] = "apples";
            echo($ar1[0]);
            echo($ar2[0]);

        ''')
        assert php_space.str_w(output[0]) == "apples"
        assert php_space.str_w(output[1]) == "zero"

    def test_py_list_is_copy_on_write_in_php2(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar2[0] = "apples";
            echo($ar1[0]);
            echo($ar2[0]);

        ''')
        assert php_space.str_w(output[0]) == "zero"
        assert php_space.str_w(output[1]) == "apples"

    def test_py_dict_is_copy_on_write_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { "aa" : "a", "bb" : "b", "cc" : "c" }
            EOD;

            $f = embed_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar1["aa"] = "apples";
            echo($ar1["aa"]);
            echo($ar2["aa"]);

        ''')
        assert php_space.str_w(output[0]) == "apples"
        assert php_space.str_w(output[1]) == "a"

    def test_py_dict_is_copy_on_write_in_php2(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { "aa" : "a", "bb" : "b", "cc" : "c" }
            EOD;

            $f = embed_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar2["aa"] = "apples";
            echo($ar1["aa"]);
            echo($ar2["aa"]);

        ''')
        assert php_space.str_w(output[0]) == "a"
        assert php_space.str_w(output[1]) == "apples"

    def test_py_list_append_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[] = "three";
            for ($i = 0; $i < 4; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert php_space.str_w(output[0]) == "zero"
        assert php_space.str_w(output[1]) == "one"
        assert php_space.str_w(output[2]) == "two"
        assert php_space.str_w(output[3]) == "three"

    def test_return_py_dict_len_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"a" : "b", "c" : "d", "e" : "f"}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo(count($ar));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_return_py_dict_vals_str_key_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"a" : "b", "c" : "d", "e" : "f"}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo($ar["a"]);
            echo($ar["c"]);
            echo($ar["e"]);
        ''')
        assert php_space.str_w(output[0]) == "b"
        assert php_space.str_w(output[1]) == "d"
        assert php_space.str_w(output[2]) == "f"

    def test_return_py_dict_vals_int_key_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {6 : "a", 7 : "b", 8 : "c"}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo($ar[8]);
            echo($ar[7]);
            echo($ar[6]);
        ''')
        assert php_space.str_w(output[0]) == "c"
        assert php_space.str_w(output[1]) == "b"
        assert php_space.str_w(output[2]) == "a"

    def test_iter_vals_py_dict_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"x" : 10, 999 : 14, "z" : -1}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $i) {
                echo($i);
            }
        ''')
        # ordering is that of python dict
        assert php_space.int_w(output[0]) == 10
        assert php_space.int_w(output[1]) == -1
        assert php_space.int_w(output[2]) == 14

    def test_iter_keys_vals_py_dict_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"x" : 10, 999 : 14, "z" : -1}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $k => $v) {
                echo("$k:$v");
            }
        ''')
        # ordering is that of python dict
        assert php_space.str_w(output[0]) == "x:10"
        assert php_space.str_w(output[1]) == "z:-1"
        assert php_space.str_w(output[2]) == "999:14"

    def test_py_dict_setitem_int_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { 0 : "one", 1 : "two", 2 : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[1] = "bumble";
            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert php_space.str_w(output[0]) == "one"
        assert php_space.str_w(output[1]) == "bumble"
        assert php_space.str_w(output[2]) == "three"

    def test_py_dict_setitem_str_in_php(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { 0 : "one", 1 : "two", 2 : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar["x"] = "bumble";
            echo($ar[0]);
            echo($ar[1]);
            echo($ar[2]);
            echo($ar["x"]);
        ''')
        assert php_space.str_w(output[0]) == "one"
        assert php_space.str_w(output[1]) == "two"
        assert php_space.str_w(output[2]) == "three"
        assert php_space.str_w(output[3]) == "bumble"

    def test_py_dict_setitem_str_in_php2(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { "one" : "one", "two" : "two", "three" : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar["two"] = "bumble";
            echo($ar["one"]);
            echo($ar["two"]);
            echo($ar["three"]);
        ''')
        assert php_space.str_w(output[0]) == "one"
        assert php_space.str_w(output[1]) == "bumble"
        assert php_space.str_w(output[2]) == "three"

    # We need to decide a semantics for [] on a wrapped Python dict/list
    @pytest.mark.xfail
    def test_py_dict_append_in_php(self):

        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { "x" : "one", "y" : "two", "z" : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[] = "bumble"; # ?!?!
                    ''')
        # XXX assert

    def test_array_type_over_php_py_boundary(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(a): return type(a) == dict";
            $f = embed_py_func($src);

            $in = array("my", "array", 2, 3);

            echo($f($in));
        ''')
        assert php_space.is_true(output[0])

    def test_array_type_over_php_py_boundary2(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(a): return type(a.as_list()) == list";
            $f = embed_py_func($src);

            $in = array(1, 2, 4, 8, 16);

            echo($f($in));
        ''')
        assert php_space.is_true(output[0])

    def test_cannot_apply_as_list_to_wrapped_mixed_key_php_array(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(a):
                try:
                    a.as_list() # boom
                except BridgeError as e:
                    return e.message
                else:
                    return "fail"
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1); // mixed keys
            echo($f($in));
        ''')

        e_str = "can only apply as_list() to a wrapped PHP array in dict form"
        assert php_space.str_w(output[0]) == e_str

    # XXX invalidation will never happen now, since we don't wrap a ref,
    # the array inside the wrapper changes without affecting the pre-as_list()
    # version of the array... Need to think about this.
    @pytest.mark.xfail # REFY
    def test_as_list_invalidates(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(arry_d):
                arry_l = arry_d.as_list()
                arry_d["x"] = 890 #non-integer keyed
                try:
                    arry_l[0] # stale!
                except BridgeError as e:
                    return e.message
                return "fail"
            EOD;

            $f = embed_py_func($src);
            $in = array(1, 2, 3); // int keys
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == \
                "Stale wrapped PHP array. No longer integer keyed!"

    # XXX We need a load more invalidation tests.
    # One for every operation that could cause a WListArrayObject to become
    # a WRDictArrayObject.

    def test_php_empty_array_len_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(a): return len(a)";
            $f = embed_py_func($src);
            $in = array();
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 0

    def test_php_int_key_array_len_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(a): return len(a.as_list())";
            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_php_mixed_key_array_len_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(ary): return len(ary)";
            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => "mixed-key", "c" => "array");
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_php_int_key_array_vals_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(ary, idx): return ary[idx]";
            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");

            echo($f($in, 0));
            echo($f($in, 1));
            echo($f($in, 2));
        ''')
        assert php_space.str_w(output[0]) == "an"
        assert php_space.str_w(output[1]) == "intkeyed"
        assert php_space.str_w(output[2]) == "array"

    def test_php_int_key_array_vals_in_python_as_list(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary, idx):
                ls = ary.as_list()
                return ls[idx]
            EOD;

            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");

            echo($f($in, 0));
            echo($f($in, 1));
            echo($f($in, 2));
        ''')
        assert php_space.str_w(output[0]) == "an"
        assert php_space.str_w(output[1]) == "intkeyed"
        assert php_space.str_w(output[2]) == "array"

    def test_php_int_key_array_len_in_python_as_list(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(ary): return len(ary.as_list())";
            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_php_mixed_key_array_vals_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = "def f(ary, idx): return ary[idx]";
            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);

            echo($f($in, "a"));
            echo($f($in, "b"));
            echo($f($in, "c"));
        ''')
        assert php_space.int_w(output[0]) == 1
        assert php_space.int_w(output[1]) == 22
        assert php_space.int_w(output[2]) == 333

    def test_php_mixed_key_array_iteritems_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = []
                for x, y in ary.iteritems():
                    ret += ["%s,%s" % (x, y)]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "a,1|b,22|c,333"

    def test_php_mixed_key_array_iterkeys_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ x for x in ary.iterkeys() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "a|b|c"

    def test_php_mixed_key_array_itervalues_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ str(x) for x in ary.itervalues() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "1|22|333"

    def test_php_int_key_array_iteritems_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = []
                for x, y in ary.iteritems():
                    ret += ["%s,%s" % (x, y)]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array(2, 1, 0);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "0,2|1,1|2,0"

    def test_php_int_key_array_iterkeys_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ str(x) for x in ary.iterkeys() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a", "b", "c");
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "0|1|2"

    def test_php_int_key_array_itervalues_in_python(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ x for x in ary.itervalues() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "x|y|z"

    def test_php_mixed_key_array_setitem_in_python_ret(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary["x"] = "y"
                return ary
            EOD;

            $f= embed_py_func($src);
            $in = array("x", "y", "z");
            $out = $f($in);
            echo $out["x"];
        ''')
        assert php_space.str_w(output[0]) == "y"

    def test_php_int_key_array_setitem_in_python_ret(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary_l = ary.as_list()
                ary_l[3] = "a"
                return ary_l
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            $out = $f($in);
            echo $out[3];
        ''')
        assert php_space.str_w(output[0]) == "a"

    def test_dict_like_py_list_works(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                if type(r) == dict:
                    return True
                else:
                    return False
            EOD;

            $f = embed_py_func($src);
            echo($f());
        ''')
        assert php_space.is_true(output[0])

    def test_dict_like_py_list_getitem(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                for i in range(3):
                    assert r[i] == i + 1
            EOD;

            $f = embed_py_func($src);
            $f();
        ''')
        # will fail if py assert raises

    def test_dict_like_py_list_setitem(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                r[0] = 666
                assert r[0] == 666
            EOD;

            $f = embed_py_func($src);
            $f();
        ''')
        # will fail if py assert raises

    def test_dict_like_py_list_length(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                return len(r)
            EOD;

            $f = embed_py_func($src);
            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_dict_like_py_list_iterkeys(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                return list(r.iterkeys())
            EOD;

            $f = embed_py_func($src);
            $a = $f();
            echo $a[0];
            echo $a[1];
            echo $a[2];
        ''')
        assert php_space.int_w(output[0]) == 0
        assert php_space.int_w(output[1]) == 1
        assert php_space.int_w(output[2]) == 2

    def test_dict_like_py_list_itervalues(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([6, 77, 888])
                return list(r.itervalues())
            EOD;

            $f = embed_py_func($src);
            $a = $f();
            echo $a[0];
            echo $a[1];
            echo $a[2];
        ''')
        assert php_space.int_w(output[0]) == 6
        assert php_space.int_w(output[1]) == 77
        assert php_space.int_w(output[2]) == 888

    def test_dict_like_py_list_iteritems(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id(["a", "b", "c"])
                return [ "%s%s" % (k, v) for k, v in r.iteritems() ]
            EOD;

            $f = embed_py_func($src);
            $a = $f();
            echo $a[0];
            echo $a[1];
            echo $a[2];
        ''')
        assert php_space.str_w(output[0]) == "0a"
        assert php_space.str_w(output[1]) == "1b"
        assert php_space.str_w(output[2]) == "2c"

    def test_dict_like_py_list_as_list(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                r_l = r.as_list()
                assert type(r_l) == list
                return r_l
            EOD;

            $f = embed_py_func($src);
            $lst = $f();
            for ($i = 0; $i < 3; $i++) {
                echo $lst[$i];
            }
        ''')
        for i in range(3):
            assert php_space.int_w(output[i]) == i + 1

    def test_php_array_as_list_val_iterator_in_py(self, php_space):
        output = self.run('''
            $a = array("a", "b", "c");

            $src = <<<EOD
            def f():
                it = iter(a.as_list())
                consume = [it.next() for x in range(3)]
                print(72 * "-")
                print(consume)
                assert consume == ["a", "b", "c"]

                try:
                    x = it.next()
                    print(x)
                    return "fail"
                except StopIteration:
                    return "ok"
            EOD;
            $f = embed_py_func($src);
            echo($f());
        ''')
        assert php_space.str_w(output[0]) == "ok"

    def test_php_array_as_list_val_iterator_in_py2(self, php_space):
        output = self.run('''
            $a = array("a", "b", "c");

            $src = <<<EOD
            def f():
                s = []
                for i in a.as_list():
                    s.append(i)
                return "".join(s)
            EOD;
            $f = embed_py_func($src);
            echo($f());
        ''')
        assert php_space.str_w(output[0]) == "abc"

    def test_str_of_py_list_passed_to_php_and_back(self, php_space):
        output = self.run('''
            $mk = embed_py_func("def mk(): return [1,2,3]");
            $str_ary = embed_py_func("def str_ary(a): return str(a)");

            $x = $mk();
            $s = $str_ary($x);
            echo($s);
        ''')
        assert php_space.str_w(output[0]) == "{0: 1, 1: 2, 2: 3}"

    def test_setdefault_on_wrapped_php_array(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def sd(ary, key, default):
                return ary.setdefault(key, default)
            EOD;
            $sd = embed_py_func($src);

            $ary = array("x" => "y");
            echo $sd($ary, "x", "k");
            echo $sd($ary, "y", "k");
        ''')
        assert php_space.str_w(output[0]) == "y"
        assert php_space.str_w(output[1]) == "k"

class TestPyPyBridgeArrayConversionsInstances(BaseTestInterpreter):

    def test_python_array_in_php_instance(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def A_construct(self, v):
                self.v = v + 1
            EOD;
            $A_construct = embed_py_func($src);

            class A {
                function __construct($v) {
                    global $A_construct;
                    $A_construct($this, $v);
                }
            }

            $a = new A(665);
            echo($a->v);
        ''')
        assert php_space.int_w(output[0]) == 666

class TestPyPyBridgeArrayConversionsInterp(BaseTestInterpreter):

    @pytest.fixture
    def interp(self):
        return self.engine.new_interp(None, None)

    def test_py_list_of_ph_array(self, interp):
        php_space, py_space = interp.space, interp.py_space

        input = [1, 2, 3, "a", "b", "c" ]
        w_php_elems = [ php_space.wrap(i) for i in input ]
        w_php_arr = php_space.new_array_from_list(w_php_elems)
        w_py_converted = w_php_arr.to_py(interp).descr_as_list(interp)

        w_py_expect = py_space.newlist([ py_space.wrap(i) for i in input ])
        assert py_space.is_true(py_space.eq(w_py_converted, w_py_expect))

    def test_py_list_of_ph_array_nested(self, interp):
        php_space, py_space = interp.space, interp.py_space

        # We will build a PHP list looking like this:
        # [ 666, False, [ 1, "a" ]]

        # inner list
        input_inner = [1, "a"]
        w_php_elems_inner = [ php_space.wrap(i) for i in input_inner ]
        w_php_arr_inner = php_space.new_array_from_list(w_php_elems_inner)

        # outer list
        input_outer = [666, False]
        w_php_elems_outer = [ php_space.wrap(i) for i in input_outer ]
        w_php_arr_outer = php_space.new_array_from_list(w_php_elems_outer)
        w_php_arr_outer.appenditem_inplace(php_space, w_php_arr_inner)

        w_py_l = w_php_arr_outer.to_py(interp)

        consts = [ py_space.wrap(i) for i in range(3) ]

        assert py_space.int_w(py_space.len(w_py_l)) == 3
        assert py_space.int_w(py_space.getitem(w_py_l, consts[0])) == 666
        assert py_space.bool_w(py_space.getitem(w_py_l, consts[1])) == False

        w_py_innr = py_space.getitem(w_py_l, consts[2])
        assert py_space.int_w(py_space.getitem(w_py_innr, consts[0])) == 1
        assert py_space.str_w(py_space.getitem(w_py_innr, consts[1])) == "a"

    # XXX Test mutating the list

    def test_ph_array_of_py_list(self, interp):
        php_space, py_space = interp.space, interp.py_space

        input = [1, 2, "wibble", "chunks", True]
        w_php_expect = php_space.new_array_from_list(
                [ php_space.wrap(x) for x in input ])

        w_py_list = py_space.newlist([ py_space.wrap(x) for x in input ])
        w_php_actual = w_py_list.to_php(interp)

        assert php_space.is_true(php_space.eq(w_php_actual, w_php_expect))

    @pytest.mark.xfail
    def test_py_list_to_php_array_nested(self, interp):
        php_space, py_space = interp.space, interp.py_space

        # Test the following list converts OK:
        # [1, 2, ["a", "b", "c"]]

        input_inner = ["a", "b", "c"]
        w_php_input_inner = [ php_space.wrap(x) for x in input_inner ]
        w_php_expect_inner = php_space.new_array_from_list(w_php_input_inner)

        input_outer = [1, 2] # and we append the inner list also
        w_php_input_outer = [ php_space.wrap(x) for x in input_outer ] + \
                [ w_php_expect_inner ]
        w_php_expect_outer = php_space.new_array_from_list(w_php_input_outer)

        w_py_input_inner = [ py_space.wrap(x) for x in input_inner ]
        w_py_list_inner = py_space.newlist(w_py_input_inner)

        w_py_list_outer = [ py_space.wrap(x) for x in input_outer ] + \
                [ w_py_list_inner ]
        w_py_list_outer = py_space.newlist(w_py_list_outer)

        w_php_got = w_py_list_outer.to_php(interp)
        assert php_space.is_true(php_space.eq(w_php_expect_outer, w_php_got))

    def test_as_list_and_mutate(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary_l = ary.as_list()
                ary_l[3] = "a"
                return ary == ary_l
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            $rv = $f($in);
            echo $rv;
        ''')
        assert not php_space.is_true(output[0])
