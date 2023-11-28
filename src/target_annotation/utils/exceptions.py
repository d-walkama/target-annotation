"""Collection of exceptions used throughout the package"""


class InvalidEnsembleId(Exception):
    """Raise when an invalid ensemble id is passed to Open Targets"""

    pass


class InvalidOntologyId(Exception):
    """Raise when an invalid ensemble id is passed to Open Targets"""

    pass


class InvalidQueryParameter(Exception):
    """Raise when an invalid parameter is passed to Open Targets"""

    pass


class InvalidStatusCode(Exception):
    """Raise when the status code does not equal 200"""

    pass


class EmptyOpenTargetsResponse(Exception):
    """Raised when targets requests an empty response"""

    pass

class EmptyPharosResponse(Exception):
    """Raised when targets requests an empty response"""

    pass



class InvalidDiseaseID(Exception):
    """Raise when an invalid disease id is passed to Open Targets"""

    pass


class InvalidTargets(Exception):
    """Raise when an invalid target/targets is/are passed to manual simulations"""

    pass


class InvalidOutcomes(Exception):
    """Raise when an invalid outcome/outcomes is/are passed to manual simulations"""

    pass
