import unittest
import contextlib
import io
import textwrap
import sys
import os
from typeguard import TypeCheckError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from target_annotation.utils import retry


class TestRetry(unittest.TestCase):
    """Unit test class for retry module"""

    def setUp(self):
        self.max_tries = 3
        self.seconds_to_wait = 0.001

        self.test_function = lambda numerator, denominator: numerator / denominator
        self.numerator = 10.0
        self.denominator = 5.0
        self.quotient = 2.0

        io_output = """
        Exception caught: division by zero. Failed attempt 1 / 3. Retrying...
        Exception caught: division by zero. Failed attempt 2 / 3. Retrying...
        Last attempt 3 / 3."""
        io_output = textwrap.dedent(io_output)
        self.io_output = [line for line in io_output.split("\n") if line != ""]

    def test_Retryer_valid_inputs(self):
        """Test invalid inputs to Retryer method"""
        for invalid_obj_type in [float, "", [], {}, None]:
            with self.assertRaises(TypeCheckError):
                retry.Retryer(
                    max_tries=invalid_obj_type,
                    seconds_to_wait=self.seconds_to_wait
                )

        for invalid_obj_type in ["", [], {}, None]:
            with self.assertRaises(TypeCheckError):
                retry.Retryer(
                    max_tries=self.max_tries,
                    seconds_to_wait=invalid_obj_type
                )

        retryer = retry.Retryer(
            max_tries=self.max_tries,
            seconds_to_wait=self.seconds_to_wait
        )

        @retryer
        def retry_test_function(*args, **kwargs):
            return self.test_function(*args, **kwargs)

        with self.assertRaises(ZeroDivisionError):
            with contextlib.redirect_stdout(None):
                retry_test_function(1, 0)

        self.assertEqual(retryer.tries, self.max_tries)

    def test_Retryer_retry_ZeroDivisionError(self):
        """
        Test if Retryer method retries the correct exception with the correct amount of
        tries
        """
        retryer = retry.Retryer(
            max_tries=self.max_tries,
            seconds_to_wait=self.seconds_to_wait,
            exception=ZeroDivisionError
        )

        @retryer
        def retry_test_function(*args, **kwargs):
            return self.test_function(*args, **kwargs)

        with self.assertRaises(ZeroDivisionError):
            with contextlib.redirect_stdout(None):
                retry_test_function(1, 0)

        self.assertEqual(retryer.tries, self.max_tries)

    def test_Retryer_no_retry_ZeroDivisionError(self):
        """Test if Retryer method doesn't retry if a specific exception is not raised"""
        retryer = retry.Retryer(
            max_tries=self.max_tries,
            seconds_to_wait=self.seconds_to_wait,
            exception=TypeError
        )

        @retryer
        def retry_test_function(*args, **kwargs):
            return self.test_function(*args, **kwargs)

        with self.assertRaises(ZeroDivisionError):
            retry_test_function(self.numerator, 0)

        self.assertEqual(retryer.tries, 1)

    def test_Retryer_no_error(self):
        """Test that Retryer method doesn't retry if there are no errors raised"""
        retryer = retry.Retryer(
            max_tries=self.max_tries,
            seconds_to_wait=self.seconds_to_wait
        )

        @retryer
        def retry_test_function(*args, **kwargs):
            return self.test_function(*args, **kwargs)

        result = retry_test_function(self.numerator, self.denominator)

        self.assertEqual(retryer.tries, 1)
        self.assertEqual(result, self.quotient)

    def test_Retryer_stdout(self):
        """Test Retryer stdout on retries"""

        retryer = retry.Retryer(
            max_tries=self.max_tries,
            seconds_to_wait=self.seconds_to_wait,
            exception=ZeroDivisionError
        )

        @retryer
        def retry_test_function(*args, **kwargs):
            return self.test_function(*args, **kwargs)

        with io.StringIO() as io_out, contextlib.redirect_stdout(io_out):
            try:
                retry_test_function(1, 0)
            except ZeroDivisionError:
                output = io_out.getvalue()

        output = [line for line in output.split("\n") if line != ""]
        self.assertEqual(output, self.io_output)
