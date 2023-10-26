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
