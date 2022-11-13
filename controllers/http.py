import json
import logging
import traceback
from datetime import date, datetime
from collections import OrderedDict

from odoo import http
from odoo.http import Response, JsonRequest, SessionExpiredException, AuthenticationError, serialize_exception
from odoo.tools import ustr
from odoo.exceptions import UserError

import werkzeug.exceptions as Wexception

_logger = logging.getLogger(__name__)


def json_default(obj):
    """
    Properly serializes date and datetime objects.
    """
    from odoo import fields
    if isinstance(obj, datetime):
        return fields.Datetime.to_string(obj)
    if isinstance(obj, date):
        return fields.Date.to_string(obj)
    return ustr(obj)


class JsonApiException(Exception):
    def __init__(self, msg, hint='', code=400):
        self.msg = msg
        self.code = code
        self.hint = hint
        super(JsonApiException, self).__init__(msg, hint, code)


class JsonApiResponse():
    def __init__(self, status='success', msg=None,
                 hint=None, result=None, http_code=200):
        self.status = status
        self.msg = msg
        self.hint = hint
        self.result = result
        self.http_code = http_code
        self._status_code = http_code

    def serialize(self) -> OrderedDict:
        response = OrderedDict([
            ('status', self.status),
        ])

        if self.msg:
            response['msg'] = self.msg

        if self.hint:
            response['hint'] = self.hint

        if self.result:
            response['result'] = self.result

        return response


class HttpJsonApiResponse():
    @staticmethod
    def error_response(error, msg, code=400, hint=None, debug=False):
        resp = OrderedDict([
            ('status', 'error'),
            ('message', msg),
            ('hint', hint or str(error)),
        ])

        if debug:
            resp['debug'] = {
                'name': str(error),
                'message': msg,
                'info': ustr(error) + ' -- ' + traceback.format_exc(),
                'arguments': list(error.args),
                'exception_type': type(error).__name__,
            }

        return http.Response(
            json.dumps(resp, default=json_default),
            status=code,
            mimetype='application/json',
        )

    @staticmethod
    def success_response(data, meta=None):
        resp = OrderedDict([
            ('status', 'success'),
            ('result', data),
        ])

        if meta:
            resp['meta'] = meta

        return http.Response(
            json.dumps(resp, default=json_default),
            status=200,
            mimetype='application/json',
        )


class JsonRequestNew(JsonRequest):
    """
    Overide of the JsonRequest
    Adding the fact that Input of json API can be an array
    ex: [{"aa":"bb"}]
    and that the output of the response can be also anything
    """

    def __init__(self, *args):
        super(JsonRequest, self).__init__(*args)
        self.params = {}
        self.jsonp_handler = None
        args = self.httprequest.args
        request = None

        request = self.httprequest.get_data().decode(self.httprequest.charset)

        try:
            self.jsonrequest = json.loads(request)
        except ValueError:
            msg = 'Invalid JSON data: %r' % (request,)
            _logger.info('%s: %s', self.httprequest.path, msg)
            raise Wexception.BadRequest(msg)

        if isinstance(self.jsonrequest, dict):
            self.params = dict(self.jsonrequest.get('params', {}))
            self.context = self.params.pop(
                'context', dict(self.session.context))
        else:
            self.params = {}
            self.context = dict(self.session.context)

    def _json_response(self, result=None, error=None):
        response = None
        status = None
        if isinstance(self.jsonrequest, dict):
            request_id = self.jsonrequest.get('id')
        else:
            request_id = None

        if error is not None and isinstance(error, JsonApiResponse):
            response = error.serialize()
            status = error.http_code

        if isinstance(result, JsonApiResponse):
            response = result.serialize()
            status = result.http_code

        if not response:
            response = {
                'jsonrpc': '2.0',
                'id': request_id,
            }

            if error is not None:
                response['error'] = error
            if result is not None:
                response['result'] = result

        mime = 'application/json'
        body = json.dumps(response, default=json_default)

        return Response(
            body, status=status or (error and error.pop(
                'http_status', 200)) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))],
        )

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to arbitrary responses. Anything returned (except None) will
           be used as response.
        """
        try:
            return super(JsonRequest, self)._handle_exception(exception)
        except Exception:
            if not isinstance(exception, SessionExpiredException):
                if exception.args and exception.args[0] == 'bus.Bus not available in test mode':
                    _logger.info(exception)
                elif isinstance(exception, (UserError,
                                            Wexception.NotFound)):
                    _logger.warning(exception)
                else:
                    _logger.exception(
                        'Exception during JSON request handling.')
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': serialize_exception(exception),
            }
            if isinstance(exception, Wexception.NotFound):
                error['http_status'] = 404
                error['code'] = 404
                error['message'] = '404: Not Found'
            if isinstance(exception, AuthenticationError):
                error['code'] = 100
                error['message'] = 'Odoo Session Invalid'
            if isinstance(exception, SessionExpiredException):
                error['code'] = 100
                error['message'] = 'Odoo Session Expired'
            if isinstance(exception, JsonApiException):
                error = JsonApiResponse(
                    'error',
                    msg=exception.msg,
                    hint=exception.hint,
                    http_code=exception.code,
                )

            return self._json_response(error=error)


_logger.info('monkey patching http.JsonRequest')
http.JsonRequest = JsonRequestNew
