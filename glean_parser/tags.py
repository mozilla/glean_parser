from typing import Dict, List, Optional
from . import util


class Tag:
    def __init__(
        self,
        name: str,
        description: str,
        defined_in: Optional[Dict] = None,
        no_lint: Optional[List[str]] = None,
        _validated: bool = False,
    ):
        # Avoid cyclical import
        from . import parser

        self.name = name
        self.description = description
        self.defined_in = defined_in
        if no_lint is None:
            no_lint = []
        self.no_lint = no_lint

        # _validated indicates whether this tag has already been jsonschema
        # validated (but not any of the Python-level validation).
        if not _validated:
            data: Dict[str, util.JSONType] = {
                "$schema": parser.TAGS_ID,
                self.name: self._serialize_input(),
            }
            for error in parser.validate(data):
                raise ValueError(error)
