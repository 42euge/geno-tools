import io

from rich.console import Console

from geno_tools.sync import terminal


CANDIDATE = {
    "name": "geno-tt",
    "stable": {
        "version": "0.8.1",
        "branch": "main",
        "sha": "b6e01f3abcd",
        "url": "https://example.test/geno-tt.git",
    },
    "active": {
        "project_version": "0.9.0",
        "branch": "feature/sync",
        "commit": "8aee348abcd",
        "source": "/tmp/geno-tt",
        "dirty": {"cached": True, "worktree": True, "untracked": 2},
        "transfer_size": 2048,
    },
}


def test_choose_one_uses_arrow_keys_and_renders_active_and_fallback_details():
    output = io.StringIO()
    console = Console(file=output, force_terminal=False, width=100)
    keys = iter([terminal.DOWN, terminal.ENTER])

    answer = terminal.choose_one(
        CANDIDATE,
        [CANDIDATE],
        read_key=lambda: next(keys),
        console=console,
    )

    assert answer == "stable"
    rendered = output.getvalue()
    assert "Dev snapshot" in rendered
    assert "0.9.0" in rendered
    assert "feature/sync" in rendered
    assert "dirty" in rendered
    assert "/tmp/geno-tt" in rendered
    assert "deactivate restores Stable" in rendered
    assert "0.8.1" in rendered
    assert "main" in rendered
    assert "2.0 KiB" in rendered


def test_choose_one_supports_up_wraparound_and_ctrl_c_cancellation():
    console = Console(file=io.StringIO(), force_terminal=False)
    keys = iter([terminal.UP, terminal.ENTER])
    assert terminal.choose_one(
        CANDIDATE,
        [CANDIDATE],
        read_key=lambda: next(keys),
        console=console,
    ) == "cancel"

    def interrupted():
        raise KeyboardInterrupt

    assert terminal.choose_one(
        CANDIDATE,
        [CANDIDATE],
        read_key=interrupted,
        console=console,
    ) == "cancel"


def test_choose_one_cleans_up_the_interactive_menu_after_selection():
    output = io.StringIO()
    console = Console(file=output, force_terminal=True, width=100)
    keys = iter([terminal.DOWN, terminal.ENTER])

    assert terminal.choose_one(
        CANDIDATE,
        [CANDIDATE],
        read_key=lambda: next(keys),
        console=console,
    ) == "stable"

    assert "\x1b[2K" in output.getvalue()
