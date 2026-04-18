from __future__ import annotations

from scripts._cli_backend import cli_arg, parse_args_json


def test_parse_args_json_supports_lists_scalars_and_invalid_json():
    assert parse_args_json('[1, "two", true, null]') == [1, 'two', True, None]
    assert parse_args_json('{"a":1}') == [{"a": 1}]
    assert parse_args_json('plain-text') == ['plain-text']


def test_cli_arg_formats_supported_types():
    assert cli_arg(True) == 'true'
    assert cli_arg(False) == 'false'
    assert cli_arg(None) == 'null'
    assert cli_arg(42) == '42'
    assert cli_arg('0xabc') == '0xabc'
    assert cli_arg([1, 2]) == '[1, 2]'
    assert cli_arg({'a': 1}) == '{"a": 1}'
