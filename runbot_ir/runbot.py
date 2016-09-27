# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2015 Odoo s.a. (<http://odoo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import operator

from collections import OrderedDict

from openerp import models, fields, api, http
from openerp.http import request
from openerp.addons.runbot.runbot import RunbotController

class runbot_repo(models.Model):
    _inherit = "runbot.repo"

    nobuild = fields.Boolean("Do not build")

    @api.model
    def update_git(self, repo):
        super(runbot_repo, self).update_git(repo=repo)
        if repo.nobuild:
            self.env['runbot.build'].search([('repo_id', '=', repo.id),
                                             ('state', '=', 'pending'),
                                             ('branch_id.sticky', '=', False)
                ]).write({'state': 'done', 'result': 'skipped'})


class RunbotCustomController(RunbotController):
    @http.route(['/runbot/ir'], type='http', auth="public", website=True)
    def irdashboard(self, refresh=None, **post):
        cr = request.cr
        RB = request.env['runbot.build']
        count = RB.search_count
        repos = request.env['runbot.repo'].search([('nobuild', "=", False)])   # respect record rules

        cr.execute("""SELECT bu.result,count(*)
                        FROM runbot_branch br
                        INNER JOIN runbot_build bu on br.id=bu.branch_id
                       WHERE br.sticky
                         AND br.repo_id in %s
                         AND bu.result IS NOT NULL
                         AND bu.date>current_date - interval '100' day
                       GROUP BY bu.result
                   """, [tuple(repos._ids)])
        statuses = [{'label':status[0], 'value':status[1]} for status in cr.fetchall() if status[0]]
        cr.execute("""SELECT bu.author,count(*) as nbr
                        FROM runbot_branch br
                        INNER JOIN runbot_build bu on br.id=bu.branch_id
                       WHERE br.sticky
                         AND br.repo_id in %s
                         AND bu.result='ok'
                         AND bu.date>current_date - interval '100' day
                       GROUP BY bu.author
                       ORDER BY nbr desc
                       limit 5
                   """, [tuple(repos._ids)])
        commiter_contest = [(commit[0], commit[1]) for commit in cr.fetchall()]
        cr.execute("""SELECT bu.author,count(*) as nbr
                        FROM runbot_branch br
                        INNER JOIN runbot_build bu on br.id=bu.branch_id
                      WHERE br.sticky
                        AND br.repo_id in %s
                        AND bu.result='ko'
                        AND bu.date>current_date - interval '100' day
                       GROUP BY bu.author
                       ORDER BY nbr desc
                       limit 3
                   """, [tuple(repos._ids)])
        broker_contest = [(commit[0], commit[1]) for commit in cr.fetchall()]
        
        qctx = {
            'refresh': refresh,
            'statuses':statuses,
            'commiter_contest': commiter_contest,
            'broker_contest': broker_contest,
            'host_stats': [],
            'pending_total': count([('state', '=', 'pending')]),
        }
        
        cr.execute("""SELECT bu.id
                        FROM runbot_branch br
                        JOIN LATERAL (SELECT *
                                        FROM runbot_build bu
                                       WHERE bu.branch_id = br.id
                                    ORDER BY id DESC
                                       LIMIT 1
                                     ) bu ON (true)
                       WHERE br.sticky
                         AND br.repo_id in %s
                    ORDER BY br.repo_id, br.branch_name, bu.id DESC
                   """, [tuple(repos._ids)])

        builds = RB.browse(map(operator.itemgetter(0), cr.fetchall()))

        repos_values = qctx['repo_dict'] = OrderedDict()
        for build in builds:
            repo = build.repo_id
            branch = build.branch_id
            r = repos_values.setdefault(repo.id, {'branches': OrderedDict()})
            if 'name' not in r:
                r.update({
                    'name': repo.name,
                    'base': repo.base,
                    'testing': count([('repo_id', '=', repo.id), ('state', '=', 'testing')]),
                    'running': count([('repo_id', '=', repo.id), ('state', '=', 'running')]),
                    'pending': count([('repo_id', '=', repo.id), ('state', '=', 'pending')]),
                })
            b = r['branches'].setdefault(branch.id, {'name': branch.branch_name, 'builds': list()})
            b['builds'].append(self.build_info(build))

        # consider host gone if no build in last 100
        build_threshold = max(builds.ids or [0]) - 100
        for result in RB.read_group([('id', '>', build_threshold)], ['host'], ['host']):
            if result['host']:
                qctx['host_stats'].append({
                    'host': result['host'],
                    'testing': count([('state', '=', 'testing'), ('host', '=', result['host'])]),
                    'running': count([('state', '=', 'running'), ('host', '=', result['host'])]),
                })

        

        return request.render("runbot_ir.ir-dashboard", qctx)
