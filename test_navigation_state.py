from navigation_state import activate_sample_workspace


def test_sample_activation_returns_to_overview_before_widget_render():
    state = {"use_sample_dataset": False, "nav_page": "Settings"}
    destination = activate_sample_workspace(state)
    assert destination == "Overview"
    assert state == {"use_sample_dataset": True, "nav_page": "Overview"}


def test_sample_activation_is_idempotent():
    state = {"use_sample_dataset": True, "nav_page": "Overview"}
    assert activate_sample_workspace(state) == "Overview"
    assert state["use_sample_dataset"] is True
