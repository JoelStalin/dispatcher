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
    
    @api.model
    def create(self, vals):
        _logger.info('Prueba Joel')
        _logger.info(vals)

        # Obtén la lista de paradas en stop_locations
        locations = vals.get('stop_locations', [])

        # Actualiza cada ubicación con el stop_number en secuencia
        for index, location in enumerate(locations, start=1):
            if isinstance(location, list) and len(location) == 3:
                # Agrega el stop_number al diccionario de detalles de cada parada
                location[2].update(stop_number=index)
            else:
                _logger.warning("Formato incorrecto en stop_locations: %s", location)

        _logger.info(vals)  # Verifica que se haya agregado correctamente stop_number

        # Crea el registro con los valores actualizados
        record = super(DispatcherRoute, self).create(vals)

        # Llama a la función de secuencia de parada si es necesario
        # record.route_id._set_stop_sequence()  # Asegura que la secuencia esté establecida para una nueva parada

        return record
    def write(self, vals):
        _logger.info("Actualizando registro: %s", self)
        _logger.info("Valores de actualización: %s", vals)

        # Si stop_locations está en los valores, actualiza el stop_number en secuencia
        if 'stop_locations' in vals:
            locations = vals.get('stop_locations', [])

            # Inicializa el índice de la secuencia
            index = 1
            for location in locations:
                # Verifica que la entrada sea una lista y tenga el formato esperado
                if isinstance(location, list) and len(location) == 3:
                    # Actualiza el stop_number en el diccionario de detalles de cada parada
                    if location[2]:
                        location[2].update(stop_number=index)
                    index += 1
                else:
                    _logger.warning("Formato incorrecto en stop_locations: %s", location)

            # Log para verificar que stop_number se haya actualizado correctamente
            _logger.info("stop_locations actualizado con secuencia: %s", locations)

        # Llama al método write original de Odoo para guardar los cambios
        result = super(DispatcherRoute, self).write(vals)

        # Opcional: vuelve a ejecutar la secuencia de paradas si es necesario
        # self.route_id._set_stop_sequence()  # Asegura que la secuencia se mantenga

        return result

    
    @api.constrains('stop_locations')
    def _check_stop_locations(self):
        if len(self.stop_locations) < 2:
            raise exceptions.ValidationError('A route must have at least two stops.')

    @api.depends('stop_locations')
    def _compute_start_end_locations(self):
        for route in self:
            if route.stop_locations:
                route.start_location = route.stop_locations[0].location_id
                route.end_location = route.stop_locations[-1].location_id
            else:
                route.start_location = False
                route.end_location = False

    # def _set_stop_sequence(self):
    #     """Set sequence numbers for each stop location in order of appearance."""
    #     for route in self:
    #         sequence = 1
    #         for stop in route.stop_locations:
    #             stop.stop_number = sequence
    #             sequence += 1

    # @api.model
    # def create(self, vals):
    #     # Create route and set stop sequence numbers
    #     record = super(DispatcherRoute, self).create(vals)
    #     record._set_stop_sequence()
    #     return record

    # def write(self, vals):
    #     res = super(DispatcherRoute, self).write(vals)
    #     if 'stop_locations' in vals:  # Only update sequence if stop_locations are modified
    #         self._set_stop_sequence()
    #     return res


class DispatcherRouteStop(models.Model):
    _name = 'dispatcher.route.stop'
    _description = 'Route Stops'

    route_id = fields.Many2one('dispatcher.route', string='Route', ondelete='cascade')
    stop_number = fields.Integer(string='Stop Number', required=True)
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    address_id = fields.Many2one('res.partner', string="Address", domain="[('type', '=', 'contact')]", required=True)
    
    # Related fields for address details
    street = fields.Char(related='address_id.street', string="Street", readonly=True)
    city = fields.Char(related='address_id.city', string="City", readonly=True)
    country_id = fields.Many2one('res.country', related='address_id.country_id', string="Country", readonly=True)


    # def write(self, vals):
    #     res = super(DispatcherRouteStop, self).write(vals)
    #     if 'stop_number' not in vals:  # Only update sequence if stop_number wasn't manually changed
    #         self.route_id._set_stop_sequence()
    #     return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string='Is a Driver', default=False)
