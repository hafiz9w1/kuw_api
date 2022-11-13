
import hashlib
import uuid
from odoo import models, fields, api


class ApiHandler(models.Model):
    _name = 'pcv.api.handler'
    _inherit = ['mail.thread']
    _description = 'Call API endpoints'

    def _default_encrypt_salt(self):
        return uuid.uuid4().hex

    name = fields.Char(required=True, tracking=True)
    user_id = fields.Many2one(
        'res.users',
        string='Related User',
        tracking=True,
    )
    root_user = fields.Boolean('Root User', tracking=True)
    active = fields.Boolean('Active', tracking=True, default=True)
    incoming_api_key = fields.Char(
        compute='_compute_credentials',
        store=True,
        tracking=True,
    )
    expire_date = fields.Datetime(string='Expiration date')
    encrypt_salt = fields.Char(
        string='Encript Salt',
        default=_default_encrypt_salt,
    )

    @api.depends('user_id', 'encrypt_salt')
    def _compute_credentials(self):
        config_env = self.env['ir.config_parameter'].sudo()
        database_uuid = config_env.get_param('database.uuid')
        for rec in self:
            api_key = database_uuid + str(rec.user_id.id) + rec.encrypt_salt
            self.incoming_api_key = hashlib.sha256(
                api_key.encode()).hexdigest()

    def button_generate_new_key(self):
        self.ensure_one()
        self.write({'encrypt_salt': uuid.uuid4().hex})
