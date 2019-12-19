from docutils.parsers.rst import Directive
from docutils import statemachine

import m2r

from glean_parser.parser import get_parameter_doc
from glean_parser.parser import get_ping_parameter_doc


class ParameterDirective(Directive):
    """Insert descriptions of parameters into the document."""
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def run(self):
        parameter = self.arguments[0]

        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1
        )

        markdown = self.get_parameter_doc(parameter)
        rst = m2r.convert(markdown)

        description = statemachine.string2lines(rst, 4, convert_whitespace=True)

        lines = [
            f'.. _{parameter}:',
            '',
            parameter,
            '`' * len(parameter),
            ''
        ] + description

        self.state_machine.insert_input(lines, source)
        return []


class MetricParameterDirective(ParameterDirective):
    """Insert descriptions of metric parameters into the document."""

    def get_parameter_doc(self, parameter):
        return get_parameter_doc(parameter)


class PingParameterDirective(ParameterDirective):
    """Insert descriptions of ping parameters into the document."""

    def get_parameter_doc(self, parameter):
        return get_ping_parameter_doc(parameter)


def setup(app):
    app.add_directive('metric_parameter', MetricParameterDirective)
    app.add_directive('ping_parameter', PingParameterDirective)
