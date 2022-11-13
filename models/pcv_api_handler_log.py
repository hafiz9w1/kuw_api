import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ApiHandlerLogs(models.Model):
    _name = 'pcv.api.handler.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'API Handle Logs'
    _rec_name = 'api_endpoint'
    _order = 'create_date DESC'

    api_endpoint = fields.Char('API Endpoint', required=True)
    request_received = fields.Text('Request Received')
    state = fields.Selection([
        ('success', 'Success'),
        ('fail', 'Fail'),
    ], string='Status', default='success')
    message = fields.Text('Message')

    @api.model
    def autovacuum(self, days=10, batch=1000):
        _logger.info('Launching API log cleaning')
        sudo = self.sudo()
        record_to_delete = sudo.get_record_to_delete(days=days, limit=batch)
        while record_to_delete:
            record_to_delete.unlink()
            record_to_delete = None
            sudo.flush()
            record_to_delete = sudo.get_record_to_delete(
                days=days, limit=batch)

        _logger.info('API log cleaning done!')
        return True

    def get_record_to_delete(self, days=10, limit=1000):
        return self.search([(
            'create_date',
            '<', datetime.now() - timedelta(days=days))], limit=limit)
