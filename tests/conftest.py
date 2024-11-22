import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-web-tests",
        action="store_true",
        default=False,
        help="Run tests that require a web connection",
    )
    parser.addoption(
        "--run-node-tests",
        action="store_true",
        default=False,
        help="Run tests that require node.js",
    )
    parser.addoption(
        "--run-ruby-tests",
        action="store_true",
        default=False,
        help="Run tests that require Ruby",
    )
    parser.addoption(
        "--run-go-tests",
        action="store_true",
        default=False,
        help="Run tests that require Go",
    )
    parser.addoption(
        "--run-rust-tests",
        action="store_true",
        default=False,
        help="Run tests that require Rust",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-web-tests"):
        skip_web = pytest.mark.skip(reason="Need --run-web-tests option to run")
        for item in items:
            if "web_dependency" in item.keywords:
                item.add_marker(skip_web)

    if not config.getoption("--run-node-tests"):
        skip_node = pytest.mark.skip(reason="Need --run-node-tests option to run")
        for item in items:
            if "node_dependency" in item.keywords:
                item.add_marker(skip_node)

    if not config.getoption("--run-ruby-tests"):
        skip_ruby = pytest.mark.skip(reason="Need --run-ruby-tests option to run")
        for item in items:
            if "ruby_dependency" in item.keywords:
                item.add_marker(skip_ruby)

    if not config.getoption("--run-go-tests"):
        skip_go = pytest.mark.skip(reason="Need --run-go-tests option to run")
        for item in items:
            if "go_dependency" in item.keywords:
                item.add_marker(skip_go)

    if not config.getoption("--run-rust-tests"):
        skip_rust = pytest.mark.skip(reason="Need --run-rust-tests option to run")
        for item in items:
            if "rust_dependency" in item.keywords:
                item.add_marker(skip_rust)
