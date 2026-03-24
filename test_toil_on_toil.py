import pytest
from toil_on_toil import i

class TestFunctions:
    def test_isalpha(self):
        assert i.walk(""" isalpha("a") """) is True
        assert i.walk(""" isalpha("z") """) is True
        assert i.walk(""" isalpha("A") """) is True
        assert i.walk(""" isalpha("Z") """) is True
        assert i.walk(""" isalpha("0") """) is False
        assert i.walk(""" isalpha("9") """) is False
        assert i.walk(""" isalpha("_") """) is False
        assert i.walk(""" isalpha("$") """) is False

    def test_isdigit(self):
        assert i.walk(""" isdigit("a") """) is False
        assert i.walk(""" isdigit("z") """) is False
        assert i.walk(""" isdigit("A") """) is False
        assert i.walk(""" isdigit("Z") """) is False
        assert i.walk(""" isdigit("0") """) is True
        assert i.walk(""" isdigit("9") """) is True
        assert i.walk(""" isdigit("_") """) is False
        assert i.walk(""" isdigit("$") """) is False

    def test_isalnum(self):
        assert i.walk(""" isalnum("a") """) is True
        assert i.walk(""" isalnum("z") """) is True
        assert i.walk(""" isalnum("A") """) is True
        assert i.walk(""" isalnum("Z") """) is True
        assert i.walk(""" isalnum("0") """) is True
        assert i.walk(""" isalnum("9") """) is True
        assert i.walk(""" isalnum("_") """) is False
        assert i.walk(""" isalnum("$") """) is False

    def test_is_name_first(self):
        assert i.walk(""" is_name_first("a") """) is True
        assert i.walk(""" is_name_first("z") """) is True
        assert i.walk(""" is_name_first("A") """) is True
        assert i.walk(""" is_name_first("Z") """) is True
        assert i.walk(""" is_name_first("0") """) is False
        assert i.walk(""" is_name_first("9") """) is False
        assert i.walk(""" is_name_first("_") """) is True
        assert i.walk(""" is_name_first("$") """) is False

    def test_is_name_rest(self):
        assert i.walk(""" is_name_rest("a") """) is True
        assert i.walk(""" is_name_rest("z") """) is True
        assert i.walk(""" is_name_rest("A") """) is True
        assert i.walk(""" is_name_rest("Z") """) is True
        assert i.walk(""" is_name_rest("0") """) is True
        assert i.walk(""" is_name_rest("9") """) is True
        assert i.walk(""" is_name_rest("_") """) is True
        assert i.walk(""" is_name_rest("$") """) is False

    def test_is_name(self):
        assert i.walk(""" is_name(sym("a")) """) is True
        assert i.walk(""" is_name(sym("_abc")) """) is True
        assert i.walk(""" is_name(sym("0a")) """) is False
        assert i.walk(""" is_name(sym("$a")) """) is False
        assert i.walk(""" is_name("a") """) is False

if __name__ == "__main__":
    pytest.main([__file__])
