from odoo import http
from odoo.http import request
from odoo.http import Response
import json

class DispatcherController(http.Controller):

    @http.route('/api/dispatcher/loads', type='http', auth='public', methods=['GET'], csrf=False)
    def get_all_loads(self, **kwargs):
        loads = request.env['dispatcher.load'].sudo().search([])
        data = [{
            'id': load.id,
            'name': load.name,
            'total_weight': load.total_weight,
            'total_distance': load.total_distance,
            'load_date': load.load_date.isoformat() if load.load_date else None,
            'state': load.state,
            'routes': [{
                'id': route.id,
                'name': route.name,
                'distance': route.distance,
                'driver_name': route.driver_name.name if route.driver_name else None,
            } for route in load.route_ids]
        } for load in loads]
        return Response(json.dumps(data), content_type='application/json')  

    @http.route('/api/dispatcher/load/status/<string:status>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_loads_by_status(self, status, **kwargs):
        valid_states = ['draft', 'in_transit', 'liberada', 'delivered', 'cancelled', 'Disponible']
        if status not in valid_states:
            error_message = {'error': f'Status {status} is not valid. Valid statuses are: {valid_states}'}
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=400)
        loads = request.env['dispatcher.load'].sudo().search([('state', '=', status)])
        data = [{
            'id': load.id,
            'name': load.name,
            'total_weight': load.total_weight,
            'total_distance': load.total_distance,
            'load_date': load.load_date.isoformat() if load.load_date else None,
            'state': load.state,
        } for load in loads]
        return Response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/api/dispatcher/load/summary', type='http', auth='public', methods=['GET'], csrf=False)
    def get_load_summary(self, **kwargs):
        loads = request.env['dispatcher.load'].sudo().search([('state', '!=', 'cancelled')])
        total_weight = sum(load.total_weight for load in loads)
        total_distance = sum(load.total_distance for load in loads)
        summary_data = {
            'total_weight': total_weight,
            'total_distance': total_distance,
            'active_load_count': len(loads)
        }
        return Response(json.dumps(summary_data), headers=[('Content-Type', 'application/json')])

    @http.route('/api/dispatcher/load/<int:load_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_load(self, load_id, **kwargs):
        load = request.env['dispatcher.load'].sudo().browse(load_id)
        if not load.exists():
            error_message = {'error': 'Load not found'}
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=404)
        data = {
            'id': load.id,
            'name': load.name,
            'total_weight': load.total_weight,
            'total_distance': load.total_distance,
            'load_date': load.load_date.isoformat() if load.load_date else None,
            'state': load.state,
            'routes': [{
                'id': route.id,
                'name': route.name,
                'distance': route.distance,
                'driver_name': route.driver_name.name if route.driver_name else None,
            } for route in load.route_ids]
        }
        return Response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/api/dispatcher/load/update_status', type='http', auth='public', methods=['POST'], csrf=False)
    def update_load_status(self, **kwargs):
        load_id = kwargs.get('load_id')
        new_status = kwargs.get('status')
        location = kwargs.get('location')
        
        # Validar parámetros requeridos
        missing_params = []
        if not load_id:
            missing_params.append('load_id')
        if not new_status:
            missing_params.append('status')
        if not location:
            missing_params.append('location')
    
        if missing_params:
            error_message = {
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'details': {
                    'load_id': load_id or 'Empty',
                    'status': new_status or 'Empty',
                    'location': location or 'Empty'
                }
            }
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=400)
        
        # Validar si el registro de carga existe
        load = request.env['dispatcher.load'].sudo().browse(int(load_id))
        if not load.exists():
            error_message = {'error': 'Load not found', 'load_id': load_id}
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=404)
        
        # Validar estado
        valid_statuses = ['in_transit', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            error_message = {
                'error': 'Invalid status.',
                'valid_statuses': valid_statuses,
                'provided_status': new_status
            }
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=400)
        
        # Crear seguimiento y actualizar estado
        tracking_data = {
            'load_id': load.id,
            'status': new_status,
            'location': location,
            'note': kwargs.get('note', '')
        }
        request.env['dispatcher.tracking'].sudo().create(tracking_data)
        load.sudo().write({'state': new_status})
        
        success_message = {
            'success': True,
            'message': 'Load status updated successfully.',
            'load_id': load.id,
            'new_status': new_status
        }
        return Response(json.dumps(success_message), headers=[('Content-Type', 'application/json')])

    @http.route('/api/dispatcher/load/<int:load_id>/consolidated_products', type='http', auth='public', methods=['GET'], csrf=False)
    def get_consolidated_products(self, load_id, **kwargs):
        load = request.env['dispatcher.load'].sudo().browse(load_id)
        if not load.exists():
            error_message = {'error': 'Load not found'}
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=404)
        orders = load.order_ids
        consolidated_products = {}
        for order in orders:
            for line in order.order_line:
                product_name = line.product_id.name.lower()
                qty = line.product_uom_qty
                price = line.price_unit
                if product_name in consolidated_products:
                    consolidated_products[product_name]['qty'] += qty
                    consolidated_products[product_name]['price'] += price * qty
                else:
                    consolidated_products[product_name] = {
                        'name': product_name,
                        'qty': qty,
                        'price': price * qty
                    }
        data = [{
            'name': product_data['name'],
            'qty': product_data['qty'],
            'price': product_data['price']
        } for product_data in consolidated_products.values()]
        return Response(json.dumps(data), headers=[('Content-Type', 'application/json')])
