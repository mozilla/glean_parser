from glean_parser import parser
from glean_parser import probes


def test_probes_match_schema():
    schema = parser.get_probes_schema()

    assert (set(probes.Probe.probes.keys()) ==
            set(schema['definitions']['probe']['properties']['type']['enum']))
