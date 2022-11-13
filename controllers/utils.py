import functools
from psycopg2 import IntegrityError
from odoo import registry
from odoo.http import request
from odoo.exceptions import ValidationError

from .http import JsonApiException, HttpJsonApiResponse, JsonApiResponse
from .auth import ApiAuthentification


# Log information of API Request
def api_route(auth=True, log_req=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            httprequest = request.httprequest
            request_type = request._request_type
            api_endpoint = httprequest.full_path
            dbname = request.db
            # format of log_message. Ex: 'Method: http POST - 200: OK'
            log_message = 'Method: %s %s - ' + '%s %s' % (request_type, httprequest.method)
            try:
                if auth:
                    ApiAuthentification.auth_api_key()
                result = func(*args, **kw)
                if log_req:
                    code = 200
                    msg = "OK"
                    log_request(api_endpoint, str(kw), dbname, log_message % (code, msg), "success")
            except Exception as err:
                if isinstance(err, JsonApiException):
                    code = 404
                    msg = err.msg
                    hint = err.hint
                elif isinstance(err, ValidationError):
                    code = 404
                    msg = str(err)
                    hint = "Check the request body"
                elif isinstance(err, IntegrityError):
                    code = 404
                    msg = str(err)
                    hint = "The record seems to be existing"
                else:
                    code = 404
                    msg = 'Unexpected error occured'
                    hint = ""

                if log_req:
                    log_request(api_endpoint, str(kw), dbname, log_message % (code, err), 'fail')

                if request_type == 'http':
                    return HttpJsonApiResponse.error_response(err, msg, hint=hint, code=code)
                else:
                    raise JsonApiException(msg=msg, hint=hint, code=code) from err
            return result
        return wrapper
    return decorator


# Add request information to database for tracking, analysis
def log_request(api_endpoint, request_received, dbname, message, status='success'):
    cr = registry(dbname).cursor()
    cr.autocommit(True)
    query = """INSERT INTO pcv_api_handler_log
    (create_date, write_date, api_endpoint, request_received, state, message)
    VALUES (now() at time zone 'UTC', now() at time zone 'UTC', %s, %s, %s, %s)"""
    params = (api_endpoint, request_received, status, message,)

    try:
        cr.execute(query, params)
    except Exception:
        # retry
        try:
            cr = registry(dbname).cursor()
            cr.autocommit(True)
            cr.execute(query, params)
        except Exception:
            cr.close()
    finally:
        cr.close()

    return True
