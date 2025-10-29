import os
import requests
import datetime
import json
import time
import logging
from dotenv import load_dotenv
load_dotenv()

dirname = os.path.dirname(__file__)

OTRS_INTEGRATOR = str(os.environ["OTRS_SERVER"]) + "nph-genericinterface.pl/Webservice/ZabbixIntegrator2/"

class Ticket:
    def __init__(self, logger: logging.Logger, info) -> None:
        self.logger: logging.Logger = logger
        self.info = info
        payload = {
                "UserLogin": os.environ["OTRS_LOGIN"],
                "Password": os.environ["OTRS_PASSWORD"]
                }
        self.Token: str = ""
        self.file_path: str = os.path.join(dirname, 'token')
        if (self.is_token_valid(self.file_path) and 
            os.path.exists(self.file_path) and 
            not os.path.getsize(self.file_path) == 0):
            with open(self.file_path, 'r') as file:
                self.Token = file.read().rstrip()
        else:
            r = self.otrs_query(payload, "SessionCreate").json()
            self.Token = r['SessionID']
            with open(self.file_path, 'w') as file:
                _ = file.write(self.Token)

    def otrs_query(self, data, operation: str) -> requests.Response:
        with requests.session() as s:
            r = s.post(OTRS_INTEGRATOR + operation, data=json.dumps(data).encode(), headers={'Content-type':'application/json'})
            return r

    def is_token_valid(self, file_path: str) -> bool:
        modification_time = os.path.getmtime(file_path)
        modification_datetime = datetime.datetime.fromtimestamp(modification_time)
        current_datetime = datetime.datetime.now()
        time_difference = current_datetime - modification_datetime
        return time_difference.total_seconds() <= 3300


    def create(self, customer, retry=2):
        self.logger.info(f"Iniciando criação do ticket!")
        
        body_text = self.info.get("message_text", "").encode("utf-8", errors="ignore").decode("utf-8")
        body_html = f"""
        <b>Canal:</b> {self.info.get('channel_id', '')}<br>
        <b>Usuário:</b> {self.info.get('user', '')}<br>
        <b>Bot ID:</b> {self.info.get('bot_id', '')}<br>
        <b>Mensagem:</b> {body_text}
        """
        data = {
            'SessionID': self.Token,
            'Ticket':  {
                'Title': f"[{str(customer).upper()}] - {body_text[:50]}",
                'Type': "Incidente",
                'Queue': "Triagem_Monitoramento_Testes",
                'Lock': "unlock",
                'ServiceID': 290,
                #'Orientation': options.orientation,
                'PriorityID': 1,
                'State': "open",
                'CustomerUser': customer,
                'Owner': "root@localhost"
            },
            'Article': {
                'SenderType': "agent",
                'IsVisibleForCustomer': 1,
                'From': "zabbix@v8.tech",
                'To': customer,
                'Subject': f"[{str(customer).upper()}] - {body_text[:50]}",
                'Body': body_html,
                'MimeType': "text/html",
                'Charset': "UTF-8",
                'TimeUnit': "0"
            },
        }


        ticket = self.otrs_query(data, "TicketCreate")

        if (ticket.status_code == 500 and retry > 0):
            self.logger.critical(f" Erro [CODE: {ticket.status_code}] na criação do ticket: {ticket.text} -- Tentativas: {3-retry}")
            time.sleep(3)
            self.create(options, retry-1)
        if (ticket.status_code != 200):
            self.logger.critical(f"Erro [CODE: {ticket.status_code}] na criação do ticket: {ticket.text}")
            raise Exception(ticket.text)
        ticket = ticket.json()
        self.logger.info(f"Ticket Criado: {ticket['Ticket']['TicketNumber']}")
        return ticket