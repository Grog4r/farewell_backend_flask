import traceback
from typing import Tuple

from flask import Flask
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from blueprints import blueprint_backend

app = Flask(__name__)
CORS(app)

app.register_blueprint(blueprint_backend)


@app.errorhandler(HTTPException)
def handle_http_error(error: HTTPException) -> Tuple[dict, int]:
    """Handle HTTP Error Response

    :param error: The error to handle
    :return: A tuple with a dict of error information to return and a status code
    """
    if not error.code:
        raise InternalServerError("Caught an HTTPError with no error code.")
    return format_error_response(error, error.code)


@app.errorhandler(ValueError)
def handle_value_error(error: ValueError) -> Tuple[dict, int]:
    """Handle Value Error Response

    :param error: The error to handle
    :return: A tuple with a dict of error information to return and a status code
    """
    return format_error_response(error, 400)


@app.errorhandler(Exception)
def handle_general_exception(error: Exception) -> Tuple[dict, int]:
    """Handle Other Errors Response

    :param error: The error to handle
    :return: A tuple with a dict of error information to return and a status code
    """
    return format_error_response(error, 500)


def format_error_response(error: Exception, error_code: int) -> Tuple[dict, int]:
    """Format Error Response

    :param error: The error to format
    :param error_code: The error code
    :param logger: The logger to log the error to
    :return: A tuple with a dict of error information to return and a status code
    """

    response = {
        "status_code": error_code,
        "error": error.__class__.__name__,
        "trace": traceback.format_exc(),
        "message": str(error),
    }
    return response, error_code


if __name__ == "__main__":
    app.run(port=8000, debug=True)
