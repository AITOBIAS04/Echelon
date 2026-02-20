"""Tests for canonical JSON utility — RFC 8785 compliance."""

import json
import math

import pytest

from theatre.engine.canonical_json import canonical_json, _normalise_float


class TestCanonicalJson:
    def test_sorted_keys(self):
        result = canonical_json({"z": 1, "a": 2, "m": 3})
        assert result == '{"a":2,"m":3,"z":1}'

    def test_nested_sorted_keys(self):
        result = canonical_json({"b": {"z": 1, "a": 2}, "a": 1})
        assert result == '{"a":1,"b":{"a":2,"z":1}}'

    def test_deeply_nested_sorting(self):
        obj = {"c": {"b": {"a": 1, "z": 2}, "a": 3}}
        result = canonical_json(obj)
        assert result == '{"c":{"a":3,"b":{"a":1,"z":2}}}'

    def test_no_whitespace(self):
        result = canonical_json({"key": "value", "num": 42})
        assert " " not in result
        assert "\n" not in result
        assert "\t" not in result

    def test_null_included(self):
        result = canonical_json({"a": None, "b": 1})
        assert result == '{"a":null,"b":1}'

    def test_array_preserves_order(self):
        result = canonical_json({"arr": [3, 1, 2]})
        assert result == '{"arr":[3,1,2]}'

    def test_empty_dict(self):
        assert canonical_json({}) == "{}"

    def test_empty_array(self):
        assert canonical_json([]) == "[]"

    def test_empty_string(self):
        assert canonical_json({"s": ""}) == '{"s":""}'

    def test_boolean_values(self):
        result = canonical_json({"t": True, "f": False})
        assert result == '{"f":false,"t":true}'

    def test_unicode_strings(self):
        result = canonical_json({"emoji": "\u00e9\u00e0\u00fc"})
        parsed = json.loads(result)
        assert parsed["emoji"] == "\u00e9\u00e0\u00fc"

    def test_tuple_treated_as_array(self):
        result = canonical_json({"t": (1, 2, 3)})
        assert result == '{"t":[1,2,3]}'


class TestFloatNormalisation:
    def test_whole_float_to_int(self):
        assert canonical_json({"v": 1.0}) == '{"v":1}'

    def test_negative_whole_float_to_int(self):
        assert canonical_json({"v": -3.0}) == '{"v":-3}'

    def test_zero_float_to_int(self):
        assert canonical_json({"v": 0.0}) == '{"v":0}'

    def test_decimal_preserved(self):
        result = canonical_json({"v": 0.5})
        assert result == '{"v":0.5}'

    def test_small_decimal(self):
        result = canonical_json({"v": 0.1})
        parsed = json.loads(result)
        assert abs(parsed["v"] - 0.1) < 1e-15

    def test_nan_rejected(self):
        with pytest.raises(ValueError, match="NaN"):
            canonical_json({"v": float("nan")})

    def test_infinity_rejected(self):
        with pytest.raises(ValueError, match="Infinity"):
            canonical_json({"v": float("inf")})

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError, match="Infinity"):
            canonical_json({"v": float("-inf")})

    def test_large_float(self):
        result = canonical_json({"v": 1e10})
        parsed = json.loads(result)
        assert parsed["v"] == 1e10

    def test_normalise_float_whole(self):
        assert _normalise_float(1.0) == 1
        assert isinstance(_normalise_float(1.0), int)

    def test_normalise_float_decimal(self):
        assert _normalise_float(0.5) == 0.5
        assert isinstance(_normalise_float(0.5), float)


class TestRoundTripDeterminism:
    """canonical_json(x) == canonical_json(json.loads(canonical_json(x)))"""

    @pytest.mark.parametrize(
        "obj",
        [
            {"a": 1, "b": 2},
            {"nested": {"z": [1, 2, 3], "a": None}},
            {"float": 0.5, "int": 42, "bool": True, "null": None},
            {"unicode": "\u00e9\u00e0\u00fc\u00f6"},
            [1, "two", 3.0, None, True],
            {"weights": {"a": 0.3, "b": 0.7}},
            {"empty": {}, "also_empty": []},
            {"deep": {"l1": {"l2": {"l3": {"l4": "value"}}}}},
        ],
    )
    def test_round_trip(self, obj):
        first = canonical_json(obj)
        second = canonical_json(json.loads(first))
        assert first == second


class TestUnsupportedTypes:
    def test_set_rejected(self):
        with pytest.raises(TypeError, match="unsupported type"):
            canonical_json({"s": {1, 2, 3}})

    def test_bytes_rejected(self):
        with pytest.raises(TypeError, match="unsupported type"):
            canonical_json({"b": b"hello"})


class TestBoolIntDistinction:
    """bool is a subclass of int in Python — must be handled correctly."""

    def test_true_is_true_not_1(self):
        result = canonical_json({"v": True})
        assert result == '{"v":true}'

    def test_false_is_false_not_0(self):
        result = canonical_json({"v": False})
        assert result == '{"v":false}'
