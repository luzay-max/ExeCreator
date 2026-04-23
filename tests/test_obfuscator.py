# -*- coding: utf-8 -*-
import pytest

from builder.utils.obfuscator import CodeObfuscator, obfuscate_code


def test_obfuscator_initialization():
    obf1 = CodeObfuscator(seed=42)
    obf2 = CodeObfuscator(seed=42)
    assert obf1._seed == obf2._seed

def test_obfuscate_keeps_syntax_valid():
    source = """
# === MERGED BUILD ===
def my_test_func(param1, param2):
    local_var = param1 + param2
    another_var = "hello world"
    return local_var, another_var

class TestClass:
    def method(self):
        a = 1
        b = 2
        return a + b
"""
    obfuscated = obfuscate_code(source, seed=123)

    # Check if the obfuscated code can be compiled without syntax errors
    try:
        compile(obfuscated, '<string>', 'exec')
    except SyntaxError as e:
        pytest.fail(f"Obfuscated code has syntax error: {e}")

    # Check if fake imports were injected
    assert "import " in obfuscated

    # Check if junk blocks were injected
    assert "if False:" in obfuscated

def test_obfuscate_renames_locals():
    source = """
def test():
    my_variable = 100
    my_variable += 50
    return my_variable
"""
    # The variable my_variable appears 3 times, should be renamed
    obfuscated = obfuscate_code(source, seed=10)
    assert "my_variable" not in obfuscated

def test_protected_names_are_not_renamed():
    source = """
def test_func():
    CONFIG = {"key": "value"}
    self = None
    True_val = True
    return CONFIG, self, True_val
"""
    obfuscated = obfuscate_code(source, seed=11)
    # These should still be present
    assert "CONFIG" in obfuscated
    assert "self" in obfuscated
    assert "True" in obfuscated

def test_encode_strings():
    source = """
def func():
    test_str = "this_is_a_test_string"
    return test_str
"""
    obf = CodeObfuscator(seed=12)
    # Force the random to always trigger string encoding for this test
    obf._rng = type("MockRNG", (), {"random": lambda self: 0.1, "sample": obf._rng.sample, "randint": obf._rng.randint})()

    obfuscated = obf.obfuscate(source)
    assert "this_is_a_test_string" not in obfuscated
    assert ".decode()" in obfuscated
