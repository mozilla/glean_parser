from pathlib import Path


from glean_parser import parser


ROOT = Path(__file__).parent


def test_parser():
    probes = parser.parse_probes(ROOT / "data" / "core.yaml")
    print(list(probes))
    assert False
