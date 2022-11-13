from schema import Schema, Optional, Or
from odoo.http import request
from ..controllers.http import http
from ..controllers.utils import api_route

from .utils import transform_name


class UserAPI(http.Controller):

    @http.route(
        '/v1/api/customers',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    @api_route()
    def getCustomer(self, **params):
        """
        API to get customers and it needs to
        authorize API Key and log request information.
        """
        query = '(id:customer_id, name:customer_name) {id, name}'
        default_order = 'id desc'
        return request.env['res.partner'].get_record(
            query, params, default_order)

    @http.route(
        '/v1/api/customers/<int:partner_id>',
        type='json',
        auth='public',
        methods=['PUT', 'PATCH'],
        csrf=False,
    )
    @api_route()
    def putCustomer(self, partner_id, **params):
        """
        API to update customers and it needs to
        authorize API Key and log request information.
        """
        rules = Schema({
            Optional('name'): str,
            Optional('street'): str,
            Optional('street2'): str,
            Optional('city'): str,
            Optional('zip'): str,
            Optional('country_id'): str,
            Optional('phone'): str,
            Optional('mobile'): str,
            Optional('email'): str,
        }, ignore_extra_keys=True)
        model = request.env['res.partner']

        return model.browse(partner_id).put_record(params, rules)

    @http.route(
        '/v1/api/customers',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    @api_route()
    def postCustomer(self, **params):
        """
        API to create new customers and it needs to authorize API Key
        and log request information.
        """
        base_rule = {
            'name': str,
            'mobile': str,
            'email': str,
        }
        model = request.env['res.partner']
        rules = Schema(Or(
            Schema(base_rule, error="Didn't match the requirements"),
            Schema({'data': [base_rule]},
                   error='Didnt match list requirements'),
        ), error='Something went wrong')

        overwrites = {
            'name': transform_name,
        }
        return model.post_record(params, rules, overwrites, data_key='data')
