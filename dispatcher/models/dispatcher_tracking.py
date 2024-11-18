from odoo import models, fields, api

class dispatcherTracking(models.Model):
    _name = 'dispatcher.tracking'
    _description = 'Dispatcher Tracking'

    load_id = fields.Many2one('dispatcher.load', string='Dispatcher Load', required=True, ondelete='cascade')
    tracking_date = fields.Datetime(string='Tracking Date', default=fields.Datetime.now)
    location = fields.Char(string='Current Location')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Dispatcher Status', default='in_transit')
    note = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        # Update the status of the load when a new tracking record is created.
        load = self.env['dispatcher.load'].browse(vals['load_id'])
        load.write({'state': vals['status']})
        return super(dispatcherTracking, self).create(vals)
