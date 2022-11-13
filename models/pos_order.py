from odoo.http import request
from ..controllers.http import http
from ..controllers.utils import api_route


class OrderAPI(http.Controller):

    @http.route(
        '/v1/api/orders',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    @api_route()
    def getOrder(self, **params):
        """
        API to get POS orders and it needs to
        authorize API Key and log request information.
        """
        query = '(id:order_id, name:order_name) {id, name}'
        default_order = 'id desc'
        return request.env['pos.order'].get_record(
            query, params, default_order)
