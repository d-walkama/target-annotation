"""Module to retry functions that make requests"""


import typing
import functools
import time
import typeguard


@typeguard.typechecked
class Retryer():
    """
    Use as decorator to retry functions with requests incase they fail

    Parameters:
    -----------
    max_tries: int
        Number of attemps to retry a function
    seconds_to_wait: int or float
        Number of seconds to wait during retry attemps. This is passed to time.sleep()

    Attributes:
    -----------
    tries: int
        Number of attempts made. Starts at 1 and stop at max_tries.
    """
    def __init__(self, max_tries: int = 3,
                 seconds_to_wait: typing.Union[int, float] = 10,
                 exception=Exception):
        self.max_tries = max_tries
        self.seconds_to_wait = seconds_to_wait
        self.exception = exception
        self.tries = 1

    def __call__(self, func: typing.Callable) -> typing.Callable:
        """
        Call method to work as decorator:

        Example:
        --------
            @Retryer()
            def function_that_needs_retries():
                pass

        Parameters:
        ----------
        func: Callable
            Function that is being tried.

        Returns:
        --------
        Callable:
            Returns retry function that wraps func
        """

        @functools.wraps(func)
        def _retry(*args, **kwargs):
            result = None
            while self.tries < self.max_tries:
                try:
                    result = func(*args, **kwargs)
                    return result
                except (self.exception,) as e:
                    msg = "Exception caught: {0}. Failed attempt {1} / {2}. Retrying..."
                    print(msg.format(e, self.tries, self.max_tries))
                    time.sleep(self.seconds_to_wait)
                self.tries += 1
            print(f"Last attempt {self.tries} / {self.max_tries}.")
            return func(*args, **kwargs)

        return _retry
