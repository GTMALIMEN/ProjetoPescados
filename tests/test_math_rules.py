from src.services.scores_calc_service import clamp, scenario_1_10


def test_clamp_limits_values():
    assert clamp(-10) == 0
    assert clamp(0) == 0
    assert clamp(50) == 50
    assert clamp(110) == 100


def test_scenario_1_10_limits_range():
    assert scenario_1_10(-5) == 1
    assert scenario_1_10(0) == 1
    assert scenario_1_10(1) == 1
    assert scenario_1_10(10) == 1
    assert scenario_1_10(11) == 2
    assert scenario_1_10(50) == 5
    assert scenario_1_10(99) == 10
    assert scenario_1_10(100) == 10
    assert scenario_1_10(150) == 10
