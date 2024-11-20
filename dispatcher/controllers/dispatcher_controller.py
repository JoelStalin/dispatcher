from odoo import http
from odoo.http import request
from odoo.http import Response
import json

class DispatcherController(http.Controller):
    
    @http.route('/api/dispatcher/load/<int:load_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_load(self, load_id):
        load = request.env['dispatcher.load'].sudo().browse(load_id)
        if not load.exists():
            error_message = {'error': 'Load not found'}
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=404)

        # Obtener las rutas asociadas al load
        routes = load.route_ids  # Asegúrate de que `route_ids` esté definido en dispatcher.load

        # Preparar datos para las rutas asociadas
        route_data = []
        for route in routes:
            route_data.append({
                'id': route.id,
                'name': route.name,
                'next_location': route.next_location.name if route.next_location else None,
                'current_position': route.current_position.name if route.current_position else None,
                'distance': route.distance,
                'driver_name': route.driver_name.name,
                'start_location': route.start_location.name if route.start_location else None,
                'end_location': route.end_location.name if route.end_location else None,
            })

        # Preparar la respuesta del load
        data = {
            'id': load.id,
            'name': load.name,
            'total_weight': load.total_weight,
            'total_distance': load.total_distance,
            'load_date': load.load_date.isoformat() if load.load_date else None,
            'state': load.state,
            'routes': route_data,  # Incluir la información de las rutas
        }

        return Response(json.dumps(data), headers=[('Content-Type', 'application/json')])

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
                price_total = line.price_total
                qty = line.product_uom_qty
                pricetax = line.price_tax
                if product_name in consolidated_products:
                    consolidated_products[product_name]['qty'] += qty
                    consolidated_products[product_name]['price'] += price_total+pricetax
                else:
                    consolidated_products[product_name] = {
                        'name': product_name,
                        'qty': qty,
                        'price': price_total
                    }
        data = [consolidated_products[product] for product in consolidated_products]
        return Response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/api/dispatcher/loads', type='http', auth='public', methods=['GET'], csrf=False)
    def get_all_loads(self, **kwargs):
        loads = request.env['dispatcher.load'].sudo().search([('company_id.code', '=', 'TRANSPORTER')])
        data = [{
            'id': load.id,
            'name': load.name,
            'total_weight': load.total_weight,
            'total_distance': load.total_distance,
            'load_date': load.load_date.isoformat() if load.load_date else None,
            'state': load.state
        } for load in loads]
        return Response(json.dumps(data), content_type='application/json')  

    @http.route('/api/dispatcher/load/update_status', type='http', auth='public', methods=['POST'], csrf=False)
    def update_load_status(self, **kwargs):
        load_id = kwargs.get('load_id')
        new_status = kwargs.get('status')
        location = kwargs.get('location')
        
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
        
        load = request.env['dispatcher.load'].sudo().browse(int(load_id))
        if not load.exists():
            error_message = {'error': 'Load not found', 'load_id': load_id}
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=404)
        
        valid_statuses = ['in_transit', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            error_message = {
                'error': 'Invalid status.',
                'valid_statuses': valid_statuses,
                'provided_status': new_status
            }
            return Response(json.dumps(error_message), headers=[('Content-Type', 'application/json')], status=400)
        
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
