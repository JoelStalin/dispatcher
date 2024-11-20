from odoo import models, fields, api, exceptions
import logging
_logger = logging.getLogger(__name__)

class DispatcherRoute(models.Model):
    _name = 'dispatcher.route'
    _description = 'Dispatcher Route'

    name = fields.Char(string='Route Name', required=True)
    load_id = fields.Many2one('dispatcher.load', string='Dispatcher Load', ondelete='cascade')
    stop_locations = fields.One2many('dispatcher.route.stop', 'route_id', string='Stop Locations')
    distance = fields.Float(string='Distance (km)', required=True)
    driver_name = fields.Many2one(
        'res.partner',
        string='Driver Name',
        domain=[('is_driver', '=', True)],
        required=True
    )
    start_location = fields.Many2one('stock.location', string='Start Location', compute='_compute_start_end_locations', store=True)
    end_location = fields.Many2one('stock.location', string='End Location', compute='_compute_start_end_locations', store=True)
    next_location = fields.Many2one('stock.location', string='Next Location', compute='_compute_next_location', store=True)
    current_position = fields.Many2one('stock.location', string='Current Position', compute='_compute_current_position', store=True)

    @api.model
    def create(self, vals):
        _logger.info('Creating DispatcherRoute')
        _logger.info(vals)

        locations = vals.get('stop_locations', [])
        for index, location in enumerate(locations, start=1):
            if isinstance(location, list) and len(location) == 3:
                location[2].update(stop_number=index)
            else:
                _logger.warning("Incorrect format in stop_locations: %s", location)

        _logger.info(vals)
        record = super(DispatcherRoute, self).create(vals)
        return record

    def write(self, vals):
        _logger.info("Updating DispatcherRoute record: %s", self)
        _logger.info("Update values: %s", vals)

        if 'stop_locations' in vals:
            locations = vals.get('stop_locations', [])
            index = 1
            for location in locations:
                if isinstance(location, list) and len(location) == 3:
                    if location[2]:
                        location[2].update(stop_number=index)
                    index += 1
                else:
                    _logger.warning("Incorrect format in stop_locations: %s", location)

            _logger.info("stop_locations updated with sequence: %s", locations)

        result = super(DispatcherRoute, self).write(vals)
        return result

    @api.constrains('stop_locations')
    def _check_stop_locations(self):
        if len(self.stop_locations) < 2:
            raise exceptions.ValidationError('A route must have at least two stops.')

    @api.depends('stop_locations')
    def _compute_start_end_locations(self):
        """
        Compute the start and end locations based on stop numbers.
        """
        for route in self:
            if route.stop_locations:
                # Find the stop with the smallest stop_number
                first_stop = min(route.stop_locations, key=lambda stop: stop.stop_number, default=None)
                # Find the stop with the largest stop_number
                last_stop = max(route.stop_locations, key=lambda stop: stop.stop_number, default=None)

                route.start_location = first_stop.location_id if first_stop else False
                route.end_location = last_stop.location_id if last_stop else False
            else:
                route.start_location = False
                route.end_location = False

    @api.depends('stop_locations.status', 'stop_locations.stop_number')
    def _compute_next_location(self):
        """
        Compute the next location based on the first stop with status 'pending'.
        """
        for route in self:
            if route.stop_locations:
                # Find the first pending stop based on stop_number
                pending_stop = route.stop_locations.filtered(lambda stop: stop.status == 'pending').sorted('stop_number')[:1]
                route.next_location = pending_stop.location_id if pending_stop else False
            else:
                route.next_location = False

    @api.depends('stop_locations.status', 'stop_locations.stop_number')
    def _compute_current_position(self):
        """
        Compute the current position based on the last completed stop or the first stop if all are pending.
        """
        for route in self:
            if route.stop_locations:
                # Filter stops with status 'completed' and get the one with the highest stop_number
                completed_stop = route.stop_locations.filtered(lambda stop: stop.status == 'completed').sorted('stop_number desc')[:1]
                # If there are completed stops, take the last one. Otherwise, take the first stop.
                if completed_stop:
                    route.current_position = completed_stop.location_id
                else:
                    # Take the first stop if all are pending
                    first_stop = route.stop_locations.sorted('stop_number')[:1]
                    route.current_position = first_stop.location_id if first_stop else False
            else:
                route.current_position = False


class DispatcherRouteStop(models.Model):
    _name = 'dispatcher.route.stop'
    _description = 'Route Stops'

    route_id = fields.Many2one('dispatcher.route', string='Route', ondelete='cascade')
    stop_number = fields.Integer(string='Stop Number', required=True)
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    address_id = fields.Many2one('res.partner', string="Address", domain="[('type', '=', 'contact')]", required=True)
    
    street = fields.Char(related='address_id.street', string="Street", readonly=True)
    city = fields.Char(related='address_id.city', string="City", readonly=True)
    country_id = fields.Many2one('res.country', related='address_id.country_id', string="Country", readonly=True)

    status = fields.Selection(
        [('pending', 'Pending'), ('completed', 'Completed')],
        string='Status',
        default='pending',
        required=True,
        help="Indicates whether the stop has been completed."
    )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string='Is a Driver', default=False)
