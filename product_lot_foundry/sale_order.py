##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: sale.py 1005 2005-07-25 08:41:42Z nicoe $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from osv import fields, osv

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True):
        res = super(sale_order_line,self).product_id_change(cr, uid, ids, pricelist, product,
            qty, uom, qty_uos, uos, name, partner_id, lang, update_tax)
        if product:
            p = self.pool.get('product.product').browse(cr, uid, product)
            res['value']['size_x'] = p.size_x
            res['value']['size_y'] = p.size_y
            res['value']['size_z'] = p.size_z
        return res
    def size_change(self, cr, uid, ids, size_x, size_y, size_z, product_id, qty, context={}):
        print size_x, size_y, size_z, product_id, qty
        if (not product_id) or not (size_x and size_y and size_z):
            return {}
        res= {}
        p = self.pool.get('product.product').browse(cr, uid, product_id)
        if size_y and size_z:
            res['product_uos_qty'] = size_x*size_y*size_z*p.weight*qty / 1000000
        else:
            res['product_uos_qty'] = size_x*p.weight*qty / 1000
        return {'value': res}


    _columns = {
        'prodlot_id' : fields.many2one('stock.production.lot', 'Production lot', help="Production lot is used to put a serial number on the production"),
        'prodlot_ids' : fields.one2many('stock.production.lot.all', 'line_id', 'Lots Assignation', help="Production lot is used to put a serial number on the production"),
        'size_x' : fields.float(digits=(16,2), string='Width'),
        'size_y' : fields.float(digits=(16,2), string='Height'),
        'size_z' : fields.float(digits=(16,2), string='Thickness'),
    }
sale_order_line()

class prod_lot_lines(osv.osv):
    _name='stock.production.lot.all'
    _columns = {
        'name': fields.float('Quantity'),
        'lot_id': fields.many2one('stock.production.lot', 'Lot'),
    }
prod_lot_lines()

class sale_order(osv.osv):
    _inherit = "sale.order"
    def action_wait(self, cr, uid, ids, *args):
        print 'Confirm'
        res = super(sale_order,self).action_wait(cr, uid, ids, *args)
        for sale in self.browse(cr, uid, ids):
            for line in sale.order_line:
                if line.prodlot_id.id:
                    self.pool.get('stock.production.lot.reservation').create(cr, uid, {
                        'name': sale.name,
                        'size_x': line.size_x,
                        'size_y': line.size_y,
                        'size_z': line.size_z,
                        'lot_id': line.prodlot_id.id
                    })
                for move in line.move_ids:
                    self.pool.get('stock.move').write(cr, uid, {
                        'prodlot_id': line.prodlot_id.id or False,
                        'name': '%.2f x %.2f x %.2f' % (line.size_x or 1.0, line.size_y or 1.0, line.size_z or 1.0)
                    })
        return res
sale_order()
