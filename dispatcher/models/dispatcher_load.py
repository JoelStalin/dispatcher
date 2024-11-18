from odoo import models, fields, api, exceptions

class  SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    dispatcher_load_id = fields.Many2one('dispatcher.load', string='load')
    
class dispatcherLoad(models.Model):
    _name = 'dispatcher.load'
    _description = 'dispatcher Load'

    name = fields.Char(string='Load Name', required=True)
    dispatcher_date = fields.Datetime(string='Dispatch Date')
    route_ids = fields.One2many('dispatcher.route', 'load_id', string='Routes', required=True)
    load_date = fields.Date('Load date', required=True)
    order_ids = fields.One2many('sale.order', 'dispatcher_load_id', string='Sale Orders', required=True)
    
    total_weight = fields.Float(string='Total Weight (kg)', compute='_compute_total_weight')
    total_distance = fields.Float(string='Total Distance (km)', compute='_compute_total_distance')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_transit', 'In Transit'),
        ('liberada' , 'Liberada'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    tracking_ids = fields.One2many('dispatcher.tracking', 'load_id', string='Tracking Updates')

        
    # transaction_ids = fields.Many2many(
    #     'transaction.model', 
    #     'dispatcher_order_transaction_rel', 
    #     'dispatcher_order_id', 
    #     'transaction_id', 
    #     string='Transactions'
    # )
    # @api.model
    # def create(self, vals):
    #     # Si no se proporciona una fecha, asigna la fecha y hora actuales
    #     if 'dispatcher_date' not in vals or not vals['dispatcher_date']:
    #         vals['dispatcher_date'] = fields.Datetime.now()
    #     record = super(dispatcherLoad, self).create(vals)
    #     record._set_stop_sequence()
    #     return record
    
    
    @api.depends('order_ids')
    def _compute_total_weight(self):
        for load in self:
            load.total_weight = 0 
            # sum(order.weight for order in load.order_ids)

    @api.depends('route_ids')
    def _compute_total_distance(self):
        for load in self:
            load.total_distance = sum(route.distance for route in load.route_ids)
    
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
        
    def action_dispatcher(self):
        for record in self:
            record.state = 'liberada'


    def action_in_transit(self):
        if self.state != 'draft':
            raise exceptions.UserError('Only draft loads can be moved to in transit.')
        self.state = 'in_transit'

    def action_delivered(self):
        if self.state != 'in_transit':
            raise exceptions.UserError('Only loads in transit can be marked as delivered.')
        self.state = 'delivered'
# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#     transaction_ids = fields.Many2many(
#         'transaction.model', 
#         'sale_order_transaction_rel', 
#         'sale_order_id', 
#         'transaction_id', 
#         string='Transactions'
#     )
