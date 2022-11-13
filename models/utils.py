from odoo import exceptions


def transform_iso_country_code_in_odoo_id(self, country_code, key=None):
    if country_code:
        country = self.env['res.country'].sudo().search([
            ('code', '=', country_code)], limit=1)
        if country:
            return key, str(country.id)
        raise exceptions.ValidationError('Country %s was not found in odoo database.' % country_code)
    return key, False


def transform_name(name, key=None, data=None):
    if name:
        return key, name.upper()
    else:
        return key, False
