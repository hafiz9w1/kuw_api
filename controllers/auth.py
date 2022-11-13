import logging

from odoo.http import request
from odoo import SUPERUSER_ID

from .http import JsonApiException

_logger = logging.getLogger(__name__)


class ApiAuthentification(object):
    @classmethod
    def auth_api_key(self):
        """
        API key authentication check
        """
        received_api_key = request.httprequest.environ.get(
            'HTTP_X_ODOO_API_KEY')
        api_handler_env = request.env['pcv.api.handler'].sudo()
        configuration_api_key = api_handler_env.search(
            [('incoming_api_key', '=', received_api_key)])

        _logger.debug(
            'Check API keys - Recieved: %s -- Source: %s' % (
                received_api_key, configuration_api_key))
        if not configuration_api_key:
            raise JsonApiException(
                msg='Failed authentification',
                hint='Check your API key',
                code=401,
            )
        if configuration_api_key.root_user:
            uid = SUPERUSER_ID
        else:
            uid = configuration_api_key.user_id.id
        request.uid = uid
