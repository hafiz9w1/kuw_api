from numpy import integer
from schema import Schema, Optional, Or
from odoo.http import request
from ..controllers.http import http
from ..controllers.utils import api_route


class InventoryAPI(http.Controller):

    @http.route(
        '/v1/api/inventory',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    @api_route()
    def getItem(self, **params):
        """
        API to get inventory and it needs to
        authorize API Key and log request information.
        """
        query = """(
            id:inventory_id,
            product_id:product_id,
            company_id:company_id,
            location_id:location_id,
            quantity:quantity)
            {
                id,
                product_id,
                company_id,
                location_id,
                quantity}
        """
        default_order = 'id desc'
        return request.env['stock.quant'].get_record(
            query, params, default_order)

    @http.route(
        '/v1/api/inventory/<int:inventory_id>',
        type='json',
        auth='public',
        methods=['PUT', 'PATCH'],
        csrf=False,
    )
    @api_route()
    def putItem(self, inventory_id, **params):
        """
        API to update inventory and it needs to
        authorize API Key and log request information.
        """
        rules = Schema({
            Optional('product_id'): str,
            Optional('company_id'): str,
            Optional('location_id'): str,
            Optional('quantity'): str,
        }, ignore_extra_keys=True)
        model = request.env['stock.quant']

        return model.browse(inventory_id).put_record(params, rules)

    @http.route(
        '/v1/api/inventory',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    @api_route()
    def postItem(self, **params):
        """
        API to create new inventory and it needs to
        authorize API Key and log request information.
        """
        base_rule = {
            'product_id': str,
            'company_id': str,
            'location_id': str,
            'quantity': str,
        }
        model = request.env['stock.quant']
        rules = Schema(Or(
            Schema(base_rule, error="Didn't match the requirements"),
            Schema({'data': [base_rule]},
                   error='Didnt match list requirements'),
        ), error='Something went wrong')

        return model.post_record(params, rules, data_key='data')
