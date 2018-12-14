from docutils.parsers.rst import Directive
from docutils import statemachine

import m2r

from glean_parser.parser import get_parameter_doc


class MetricParameterDirective(Directive):
    """Insert descriptions of metric parameters into the document."""
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def run(self):
        parameter = self.arguments[0]

        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1
        )

        markdown = get_parameter_doc(parameter)
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


def setup(app):
    app.add_directive('metric_parameter', MetricParameterDirective)
