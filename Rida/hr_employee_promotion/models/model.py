from odoo import fields, api, models, _
import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError


class employee_promotion(models.Model):
	_name = 'employee.promotion'
	_description = 'Employee Promotion'
	_rec_name = 'employee_id'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	@api.constrains('grade_id', 'n_grade_id')
	def _check_sequence(self):
		if self.grade_id and self.n_grade_id and (self.n_grade_id.sequence > self.grade_id.sequence):
			raise UserError('New Grade Is Less Than The Current Grade')

	name = fields.Char('Reference')
	date = fields.Date("Date", default=datetime.datetime.now().date(), readonly=True)
	employee_id = fields.Many2one("hr.employee", "Employee", required=True)
	department_id = fields.Many2one("hr.department", "Department", readonly=True, compute="_onchange_employee_id",store=True)
	job_id = fields.Many2one("hr.job", "Job Title", readonly=True, compute="_onchange_employee_id", store=True)
	n_department_id = fields.Many2one("hr.department", "New Department", )
	n_job_id = fields.Many2one("hr.job", "New Job Title")
	state = fields.Selection([
		('draft', 'Draft'),
		('hr_manager_approve', 'Waiting Hr Manager Approval'),
		('reject', 'Rejected'),
		('approve', 'Approved')
	], default='draft', track_visibility='onchnage')
	company_id = fields.Many2one("res.company", string="Company", related="employee_id.company_id", store=True,readonly=True)
	note = fields.Text("Note")
	grade_id = fields.Many2one('hr.grade.configuration', 'Grade', compute="_onchange_employee_id", store=True)
	n_grade_id = fields.Many2one('hr.grade.configuration', 'New Grade')
	grade_promotion = fields.Boolean('Grade Promotion')
	include_department_rotation = fields.Boolean('Department Rotation')
	include_job_rotation = fields.Boolean('Job Rotation')

	basic = fields.Float("Basic", compute="_onchange_employee_id", store=True)
	total_allowances = fields.Float("Total Allowances", compute="_onchange_employee_id", store=True)

	new_basic = fields.Float("New Basic")
	new_total_allowances = fields.Float("New Total Allowances",compute="get_new_total_allowances", store=True,)

	is_salary_promotion = fields.Boolean('Salary Promotion')
	rotation_ids = fields.One2many('employee.rotation.line', 'promotion_id',compute ='_get_rotation_ids_domain', store=True)
	salary_increase_ids = fields.One2many('hr.salary.increase.line', 'promotion_id')
	grade_line_id = fields.One2many(comodel_name='hr.grade.line', inverse_name='promotion_id', string='Old Benefits')
	grade_line_id_promotion = fields.One2many(comodel_name='hr.grade.line.promotion', inverse_name='promotion_id', string='New Benefits')
	old_band = fields.Many2one(comodel_name='job.band', string='Job Band')
	new_band = fields.Many2one(comodel_name='job.band', string='New Job Band')
	
	@api.depends('employee_id')
	def _get_rotation_ids_domain(self):
		for rec in self:
			rotation_link=[]
			rotation_line = self.env['employee.rotation']
			rotation = rotation_line.search([('employee_id','=',rec.employee_id.id)])
			if rotation:
				lines = [(5,0,0)]
				for ro in rotation:
					vals = {
						'employee_id':ro.employee_id.id,
						'department_id':ro.department_id.id,
						'n_department_id':ro.n_department_id.id,
						'job_id':ro.job_id.id,
						'n_job_id':ro.n_job_id.id,
					}
					lines.append((0,0,vals))
				rec.rotation_ids = lines
					# rotation_link = ro.rotation


	@api.onchange('employee_id')
	def _onchange_employee_id(self):
			# self.grade_line_id.unlink()
			# self.grade_line_id_promotion.unlink()
			self.department_id = self.employee_id.department_id
			self.job_id = self.employee_id.job_id
			self.old_band = self.employee_id.band_id
			self.grade_id = self.employee_id.contract_id.grade_id or False
			self.basic = self.employee_id.contract_id.basic
			self.total_allowances = self.employee_id.contract_id.total_allowance
			contract_grade = self.employee_id.contract_id or False 
			# raise UserError(contract_grade)
			lines = [(5, 0, 0)]
			lines2 = [(5, 0, 0)]
			if contract_grade:
				for line in contract_grade.grade_line_id:
					vals = {
						'name': line.name,
						'type': line.type,
						'code': line.code,
						'percentage': line.percentage,
						'amount': line.amount,
						'promotion_id': self.id
					}
					lines.append((0, 0, vals))
					vals2 = {
						'name': line.name,
						'type': line.type,
						'code': line.code,
						'percentage': line.percentage,
						'amount': line.amount,
						'promotion_id': self.id
					}
					lines2.append((0, 0, vals2))
				self.grade_line_id = lines
				self.grade_line_id_promotion = lines2
			else:
				self.grade_line_id.unlink()
				self.grade_line_id_promotion.unlink()
				# pass

	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise UserError("Only draft records can be deleted!")
		super(employee_promotion, self).unlink()

	# @api.depends('n_grade_id','employee_id')
	@api.onchange('n_grade_id')
	def onchange_n_grade_id(self):
		if self.n_grade_id and self.grade_id:
			self.new_basic = self.n_grade_id.basic
			lines = [(5, 0, 0)]
			for line in self.n_grade_id.grade_line_id:
				vals = {
						'name': line.name,
						'type': line.type,
						'code': line.code,
						'percentage': line.percentage,
						'amount': line.amount,
						'promotion_id': self.id
					}
				lines.append((0, 0, vals))
			self.grade_line_id_promotion = lines
	

	@api.onchange('new_basic','grade_line_id_promotion')
	def get_amount_perecentage(self):
		for rec in self:
			for line in rec.grade_line_id_promotion:
				if line.type == 'percentage':
					line.amount = ((line.percentage)/100) * rec.new_basic
				else:
					pass


	@api.depends('grade_line_id_promotion.amount','grade_line_id_promotion','new_basic')
	def get_new_total_allowances(self):
		for rec in self:
			total = 0
			for line in rec.grade_line_id_promotion:
				# if line.type == 'fixed':
				total += line.amount
				# elif line.type == 'percentage':
				# total += ((line.amount)/100) * rec.new_basic
			rec.new_total_allowances = total 
			
			
	def submit(self):
		for rec in self:
			hr_manager_user = []
			hr_manager_user = rec.env.ref('hr.group_hr_manager').users
			# hr_managers = rec.env.ref('hr.group_hr_manager').users.mapped('employee_ids')
			emails = [manager.work_email for manager in hr_manager_user]
			# rec.requested_by = rec.env.user.employee_id
			mail_content = "  Hello  "  ",<br> There is a promotion request for employee " + str(rec.employee_id.name) \
				+ " with employee code of "  + str(rec.employee_id.emp_code) + " Please review this promotion request for Approval."
			main_content = {
				'subject': _('Promotion of %s') % (rec.employee_id.name),
				'author_id': rec.env.user.partner_id.id,
				'body_html': mail_content,
				'email_to': emails,
			}
			rec.env['mail.mail'].sudo().create(main_content).send()
			for manager in hr_manager_user:
				rec.activity_schedule('hr_employee_promotion.mail_act_promotion_approval', user_id=manager.id)
			rec.state = 'hr_manager_approve'

	def hr_manager_approve(self):
		self.sudo().action_hr_manager_approve()
		email = self.create_uid.employee_id.work_email
		mail_content = "  Hello  "  ",<br> The promotion request for employee " + str(self.employee_id.name) \
					   + " with employee code of " + str(self.employee_id.emp_code) + " was approved by the HR manager."
		main_content = {
			'subject': _('Promotion of %s') % (self.employee_id.name),
			'author_id': self.env.user.partner_id.id,
			'body_html': mail_content,
			'email_to': email,
		}
		self.env['mail.mail'].sudo().create(main_content).send()
		self.state = "approve"
		self.activity_unlink(['hr_employee_promotion.mail_act_promotion_approval'])
		self.activity_unlink(['hr_employee_promotion.mail_act_promotion_reject'])

	def action_hr_manager_approve(self):
		for rec in self:
			if rec.n_department_id and rec.department_id != rec.n_department_id:
				rec.employee_id.department_id = rec.n_department_id
				rec.employee_id.contract_id.department_id = rec.n_department_id
				rec.employee_id.parent_id = rec.n_department_id.manager_id
			if rec.n_job_id and rec.job_id != rec.n_job_id:
				rec.employee_id.job_id = rec.n_job_id
				rec.employee_id.contract_id.job_id = rec.n_job_id
			if rec.n_grade_id and rec.grade_id != rec.n_grade_id:
				rec.employee_id.contract_id.grade_id = rec.n_grade_id
			if rec.new_band and rec.old_band != rec.new_band:
				rec.employee_id.band_id = rec.new_band
			if rec.is_salary_promotion == True:
				rec.employee_id.contract_id.basic = rec.new_basic
				rec.employee_id.contract_id.grade_line_id.unlink()
				for line in rec.grade_line_id_promotion:
					self.env['hr.grade.line'].create({
						'name': line.name,
						'type': line.type,
						'code': line.code,
						'percentage': line.percentage,
						'amount': line.amount,
						'contract_id': rec.employee_id.contract_id.id
					})
			rec.state = 'approve'
			if rec.n_department_id:
				self.sudo().create_employee_rotation()
			if rec.is_salary_promotion == True:
				self.sudo().create_salary_increase()

	def reject_button(self):
		for rec in self:
			email = self.create_uid.employee_id.work_email
			mail_content = "  Hello  "  ",<br> The promotion request for employee " + str(self.employee_id.name) \
						   + " with employee code of " + str(
				self.employee_id.emp_code) + " was Rejected by the HR manager."
			main_content = {
				'subject': _('Promotion of %s') % (self.employee_id.name),
				'author_id': self.env.user.partner_id.id,
				'body_html': mail_content,
				'email_to': email,
			}
			self.env['mail.mail'].sudo().create(main_content).send()
			rec.state = 'reject'
			rec.activity_unlink(['hr_employee_promotion.mail_act_promotion_approval'])
			rec.activity_unlink(['hr_employee_promotion.mail_act_promotion_reject'])

	def reset_button(self):
		for rec in self:
			rec.state = 'draft'


	def action_reset_draft(self):
		for rec in self:
			rec.state = 'draft'

	def create_employee_rotation(self):
		rotation = self.env['employee.rotation']
		for rec in self:
			employee_id = rec.employee_id.id or False
			department_id = rec.department_id
			n_department_id = rec.n_department_id
			job_id = rec.job_id.id or False
			n_job_id = rec.n_job_id.id or False
			vals = {
				'promotion_id': rec.id,
				'employee_id': employee_id,
				'date': datetime.datetime.today(),
				'department_id': department_id.id or False,
				'n_department_id': n_department_id.id or False,
				'job_id': job_id,
				'n_job_id': n_job_id,
				'state': 'hr_manager'
			}
			current_item = [rec.department_id, rec.job_id]
			new_item = [rec.n_department_id, rec.n_job_id]

			if not all(item in current_item for item in new_item):
				rotation.create(vals)
			return

	def create_salary_increase(self):
		increase = self.env['hr.salary.increase']
		increase_line = self.env['hr.salary.increase.line']
		for rec in self:
			employee_id = rec.employee_id.id or False
			vals = {
				'date': datetime.datetime.now(),
				'date_applied_on': datetime.datetime.now(),
				'state': 'confirm',
				'name': 'Promotion Salary for' + ' ' + rec.employee_id.name,
				'increase_type': 'promotion',
				'applied_for': 'employee',
			}

			current_item = [rec.basic]
			new_item = [rec.new_basic]
			if not all(item in current_item for item in new_item):
				increase_id = increase.create(vals)
				if not increase_id:
					return
				vals_line = {
					'increase_id': increase_id.id,
					'promotion_id': rec.id,
					'employee_id': employee_id,
					'basic': rec.basic,
					'new_basic': rec.new_basic,
					'amount': rec.new_basic - rec.basic,
				}
				increase_line.create(vals_line)
			return


class EmployeeRotation(models.Model):
	_inherit = 'employee.rotation'

	promotion_id = fields.Many2one('employee.promotion', 'Promotion')


class SalaryIncreaseLine(models.Model):
	_inherit = 'hr.salary.increase.line'

	promotion_id = fields.Many2one('employee.promotion', 'Promotion')


class hrEmployee(models.Model):
	_inherit = 'hr.employee'

	def compute_promotion_count(self):
		for record in self:
			record.promotion_count = self.env['employee.promotion'].search_count(
				[('employee_id', '=', self.id)])

	promotion_count = fields.Integer(compute='compute_promotion_count')

	def get_promotion(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'Promotion',
			'view_mode': 'tree,form',
			'res_model': 'employee.promotion',
			'domain': [('employee_id', '=', self.id)],
			'context': "{'create': False}"
		}


class HRGradeLine(models.Model):
	_inherit = 'hr.grade.line'

	promotion_id = fields.Many2one(comodel_name='employee.promotion', string='Promotion')

class HRGradeLinePromotion(models.Model):
	_name = 'hr.grade.line.promotion'
	_inherit = 'hr.grade.line'
	
class HRPromotionLine(models.Model):
	_name = 'employee.rotation.line'

	employee_id = fields.Many2one("hr.employee", "Employee", required=True)
	department_id = fields.Many2one("hr.department","Department",)
	job_id = fields.Many2one("hr.job", "Job Title",)
	n_department_id = fields.Many2one("hr.department", "New Department")
	n_job_id = fields.Many2one("hr.job", "New Job Title")
	company_id = fields.Many2one("res.company", string="Company")
	new_company = fields.Many2one("res.company", string="New Company")
	note = fields.Text("Note")
	movement_type = fields.Selection(string='Movement Type', selection=[('rotation', 'Rotation'), ('transfare', 'Transfer'),('temp_transfare', 'Temporary Transfer'), ('secondment', 'Secondment'),('to_project', 'Assign to Project')])
	promotion_id = fields.Many2one(comodel_name='employee.promotion', string='Promotion')
