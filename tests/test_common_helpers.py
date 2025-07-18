import pytest
from src.shared.common_helpers import (
    get_nested_value,
    set_nested_value,
    __get_nested_dict_value,
    __set_nested_dict_value,
    __get_nested_list_value,
    __set_nested_list_value,
)

def test_get_nested_dict_value():
    data = {"level1": {"level2": {"level3": "value"}}}
    assert __get_nested_dict_value(data, ["level1", "level2", "level3"]) == "value"
    assert __get_nested_dict_value(data, ["level1", "level2", "missing"]) is None
    assert __get_nested_dict_value(data, ["missing"]) is None

def test_set_nested_dict_value():
    data = {"level1": {"level2": {}}}
    updated_data = __set_nested_dict_value(data, ["level1", "level2", "level3"], "new_value")
    assert updated_data["level1"]["level2"]["level3"] == "new_value"
    assert data == updated_data  # Ensure the original dictionary is updated

def test_get_nested_list_value():
    data = [[1, 2, [3, 4]], [5, 6]]
    assert __get_nested_list_value(data, [0, 2, 1]) == 4
    assert __get_nested_list_value(data, [1, 0]) == 5
    assert __get_nested_list_value(data, [2]) is None

def test_set_nested_list_value():
    data = [[1, 2, [3, 4]], [5, 6]]
    updated_data = __set_nested_list_value(data, [0, 2, 1], 99)
    assert updated_data[0][2][1] == 99
    assert data == updated_data  # Ensure the original list is updated

def test_get_nested_value_dict():
    data = {"level1": {"level2": {"level3": "value"}}}
    assert get_nested_value(data, "level1", "level2", "level3") == "value"
    assert get_nested_value(data, "level1.level2.level3") == "value"
    assert get_nested_value(data, "level1", "missing") is None

def test_get_nested_value_list():
    data = [[1, 2, [3, 4]], [5, 6]]
    assert get_nested_value(data, 0, 2, 1) == 4
    # assert get_nested_value(data, [0, 2, 1]) == 4
    assert get_nested_value(data, 2) is None

def test_set_nested_value_dict():
    data = {"level1": {"level2": {}}}
    updated_data = set_nested_value(data, "new_value", "level1", "level2", "level3")
    assert updated_data["level1"]["level2"]["level3"] == "new_value"
    assert data == updated_data  # Ensure the original dictionary is updated

def test_set_nested_value_list():
    data = [[1, 2, [3, 4]], [5, 6]]
    updated_data = set_nested_value(data, 99, 0, 2, 1)
    assert updated_data[0][2][1] == 99
    assert data == updated_data  # Ensure the original list is updated