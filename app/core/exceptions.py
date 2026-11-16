
class TestStopped(RuntimeError):
    """
    Raised when a test sequence is stopped because
    a measurement result does not meet its criteria.
    """
    pass
