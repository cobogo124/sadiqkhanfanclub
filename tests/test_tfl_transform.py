from data_retrieval.tfl_transform import bool_from_tfl_value, split_zone_string, uri_safe_fragment


def test_split_zone_string_handles_boundary_zone_values() -> None:
    assert split_zone_string("2/3") == ["2", "3"]
    assert split_zone_string("5+6") == ["5", "6"]
    assert split_zone_string("1") == ["1"]
    assert split_zone_string("NA") == []


def test_bool_from_tfl_value_handles_yes_no_and_numeric_text() -> None:
    assert bool_from_tfl_value("yes") is True
    assert bool_from_tfl_value("no") is False
    assert bool_from_tfl_value("2") is True
    assert bool_from_tfl_value("0") is False
    assert bool_from_tfl_value("0 on platforms, 0 in ticket halls, 0 elsewhere") is False


def test_uri_safe_fragment_normalizes_station_names() -> None:
    assert uri_safe_fragment("King's Cross St. Pancras Underground Station") == "kings_cross_st_pancras_underground_station"
