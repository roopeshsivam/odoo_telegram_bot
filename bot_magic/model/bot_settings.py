from openerp import models, fields, api, _
from odoo.exceptions import UserError, AccessError, Warning
import requests


class CompanyBotID(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    bot_id = fields.Char(string="Telegram Bot ID")


class TelegramUser(models.Model):
    _inherit = 'res.users'
    _name = 'res.users'

    tel_chat_id = fields.Char(string="Telegram Chat ID")

    def get_chat_id(self):
        bot_id = self.company_id.bot_id
        send_message = 'https://api.telegram.org/'+bot_id+'/getUpdates?offset=-1'
        response = requests.get(send_message)
        response = response.json()
        login = response.get('result')[0].get('message').get('text')
        tel_chat_id = response.get('result')[0].get(
            'message').get('chat').get('id')
        if tel_chat_id and str(self.login) == str(login):
            self.write({'tel_chat_id': tel_chat_id})
        else:
            raise UserError(str(response))


class TelegramGroup(models.Model):
    _inherit = 'res.groups'
    _name = 'res.groups'

    tel_chat_id = fields.Char(string="Telegram Chat ID")

    def get_chat_id(self):
        bot_id = self.env.user.company_id.bot_id
        send_message = 'https://api.telegram.org/'+bot_id+'/getUpdates?offset=-1'
        response = requests.get(send_message)
        response = response.json()
        name = response.get('result')[0].get('message').get('text')
        tel_chat_id = response.get('result')[0].get(
            'message').get('chat').get('id')
        if tel_chat_id and self.name == str(name):
            self.write({'tel_chat_id': tel_chat_id})
        else:
            raise UserError(str(response))


class TelegramMessage(models.Model):
    _name = 'telegram.messages'

    message_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('fail', 'Failed'),
    ], default='draft', copy=False)

    name = fields.Char(string="Name")
    message_type = fields.Selection([
        ('user', 'User'),
        ('group', 'Group'),
    ])
    user_id = fields.Many2one('res.users', string='User')
    group_id = fields.Many2one('res.groups', string='Group')
    message = fields.Text(string='Message')
    response = fields.Text(string='Repsonse')
    message_id = fields.Char(string="Message ID")
    model_name = fields.Char(string="Model Name")
    model_id = fields.Char(string="Model ID")

    def send_message(self):
        if self.message_type == "user":
            chat_id = self.user_id.tel_chat_id
            bot_id = self.user_id.company_id.bot_id
        elif self.message_type == "group":
            chat_id = self.group_id.tel_chat_id
            bot_id = self.env.user.company_id.bot_id

        if chat_id and bot_id:
            base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            subject = '<b>'+self.name+'</b>%0A'
            message1 = self.message+'%0A'
            message2 = '-'
            if self.model_name and self.model_id:
                message2 = '<a href="'+base_url+'/mail/view?model=' + \
                    self.model_name+'%26amp;res_id=' + \
                    str(self.model_id)+'">Link</a>'
            message = subject+message1+message2
            send_text = 'https://api.telegram.org/' + bot_id + \
                '/sendMessage?chat_id=' + chat_id + '&parse_mode=HTML&text=' + message
            response = requests.get(send_text)
            response = response.json()
            self.response = str(response)
            if response.get('ok'):
                self.message_status = 'sent'
                self.message_id = response.get('result').get('message_id')
            else:
                self.message_status = 'fail'
        return True
