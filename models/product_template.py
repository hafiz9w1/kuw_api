from schema import Schema, Optional, Or
from odoo.http import request
from ..controllers.http import http
from ..controllers.utils import api_route

from .utils import transform_name


class ItemAPI(http.Controller):

    @http.route(
        '/v1/api/items',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    @api_route()
    def getItem(self, **params):
        """
        API to get Items (products) and it needs to
        authorize API Key and log request information.
        """
        query = '(id:item_id, name:item_name) {id, name}'
        default_order = 'id desc'
        return request.env['product.template'].get_record(
            query, params, default_order)

    @http.route(
        '/v1/api/items/<int:item_id>',
        type='json',
        auth='public',
        methods=['PUT', 'PATCH'],
        csrf=False,
    )
    @api_route()
    def putItem(self, item_id, **params):
        """
        API to update items (products) and it needs to
        authorize API Key and log request information.
        """
        rules = Schema({
            Optional('name'): str,
            Optional('list_price'): float,
            Optional('standard_price'): float,
        }, ignore_extra_keys=True)
        model = request.env['product.template']

        return model.browse(item_id).put_record(params, rules)

    @http.route(
        '/v1/api/items',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    @api_route()
    def postItem(self, **params):
        """
        API to create new Items (products) and it needs to
        authorize API Key and log request information.
        """
        base_rule = {
            'name': str,
        }
        model = request.env['product.template']
        rules = Schema(Or(
            Schema(base_rule, error="Didn't match the requirements"),
            Schema({'data': [base_rule]},
                   error='Didnt match list requirements'),
        ), error='Something went wrong')

        overwrites = {
            'name': transform_name,
        }
        return model.post_record(params, rules, overwrites, data_key='data')
