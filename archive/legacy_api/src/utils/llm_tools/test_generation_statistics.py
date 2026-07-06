import pytest

from src.utils.llm_tools.generation_statistics import GenerationStatistics


def test_init():
    gs = GenerationStatistics(1, 2, 3, 4, 5, "test-model")
    assert gs.input_time == 1
    assert gs.output_time == 2
    assert gs.input_tokens == 3
    assert gs.output_tokens == 4
    assert gs.total_time == 5
    assert gs.model_name == "test-model"


def test_get_input_speed():
    gs = GenerationStatistics(input_time=2, input_tokens=10)
    assert gs.get_input_speed() == 5
    gs.input_time = 0
    assert gs.get_input_speed() == 0


def test_get_output_speed():
    gs = GenerationStatistics(output_time=4, output_tokens=20)
    assert gs.get_output_speed() == 5
    gs.output_time = 0
    assert gs.get_output_speed() == 0


def test_add():
    gs1 = GenerationStatistics(1, 2, 3, 4, 5)
    gs2 = GenerationStatistics(5, 4, 3, 2, 1)
    gs1.add(gs2)
    assert gs1.input_time == 6
    assert gs1.output_time == 6
    assert gs1.input_tokens == 6
    assert gs1.output_tokens == 6
    assert gs1.total_time == 6

    with pytest.raises(TypeError):
        gs1.add("not a GenerationStatistics object")


def test_str():
    gs = GenerationStatistics(1, 2, 10, 20, 5, "test-model")
    result = str(gs)
    assert "10.00 T/s ⚡" in result
    assert "Round trip time: 5.00s" in result
    assert "Model: test-model" in result
    assert "| Speed (T/s)     | 10.00" in result
    assert "| 10.00" in result
    assert "| 6.00" in result
    assert "| Tokens          | 10" in result
    assert "| 20" in result
    assert "| 30" in result
    assert "| Inference Time (s) | 1.00" in result
    assert "| 2.00" in result
    assert "| 5.00" in result
