"""Small, testable navigation state transitions for the Streamlit workspace."""


def activate_sample_workspace(state):
    """Activate the local sample and return the user to its Overview."""
    state["use_sample_dataset"] = True
    state["nav_page"] = "Overview"
    return state["nav_page"]
