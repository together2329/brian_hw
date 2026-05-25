from lib.iteration_control import detect_completion_signal


def test_final_answer_line_is_completion_signal():
    assert detect_completion_signal("Final Answer: done")


def test_final_answer_mention_is_not_completion_signal():
    assert not detect_completion_signal("When done, include Final Answer: <summary>.")

