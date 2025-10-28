# otrs_integration.py
import os
import requests
import datetime
import json
import time
from types import SimpleNamespace
from dotenv import load_dotenv
from logger import logger

load_dotenv()

OTRS_SERVER = str(os.environ.get("OTRS_SERVER", "")) + "nph-genericinterface.pl/Webservice/ZabbixIntegrator2/"
TOKEN_FILE = os.environ.get("OTRS_TOKEN_FILE", "/etc/zabbix/alertscripts/otrs-integration/src/token")

class OTRSTicketClient:
    def __init__(self) -> None:
        payload = {
            "UserLogin": os.environ.get("OTRS_LOGIN", ""),
            "Password": os.environ.get("OTRS_PASSWORD", "")
        }
        self.Token = ""
        self.file_path = TOKEN_FILE
        try:
            if os.path.exists(self.file_path) and self.is_token_recent(self.file_path):
                with open(self.file_path, 'r') as file:
                    self.Token = file.read().rstrip()
            else:
                r = self.otrs_query(payload, "SessionCreate").json()
                self.Token = r.get('SessionID', '')
                try:
                    os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                    with open(self.file_path, 'w') as file:
                        file.write(self.Token)
                except Exception:
                    logger.warning("Não foi possível gravar token em disco (permissões?)")
        except Exception as e:
            logger.exception("Erro inicializando OTRS token: %s", e)
            raise

    def is_token_recent(self, file_path):
        try:
            modification_time = os.path.getmtime(file_path)
            modification_datetime = datetime.datetime.fromtimestamp(modification_time)
            current_datetime = datetime.datetime.now()
            time_difference = current_datetime - modification_datetime
            return time_difference.total_seconds() <= 3300
        except Exception:
            return False

    def otrs_query(self, data, operation):
        url = OTRS_SERVER + operation
        with requests.session() as s:
            r = s.post(url, data=json.dumps(data).encode(), headers={'Content-type':'application/json'}, timeout=30)
            return r

    def create(self, options: SimpleNamespace, retry=2):
        logger.info(f"[Slack -> OTRS] Criando ticket - origem slack message")
        body = options.body if hasattr(options, 'body') else ""
        template_path = os.path.join(os.path.dirname(__file__), 'body.html')
        if not body and os.path.exists(template_path):
            with open(template_path, 'r') as f:
                tpl = f.read()
            body = tpl.format(**{k: getattr(options, k, "") for k in dir(options) if not k.startswith("_")})

        data = {
            'SessionID': self.Token,
            'Ticket':  {
                'Title': options.title,
                'Type': options.type if getattr(options, 'type', None) else "Incidente",
                'Queue': getattr(options, 'queue', os.environ.get("OTRS_QUEUE", "")),
                'Lock': "unlock",
                'ServiceID': getattr(options, 'service_id', os.environ.get("OTRS_SERVICE", "")),
                'Orientation': getattr(options, 'orientation', ""),
                'PriorityID': getattr(options, 'priority', "2"),
                'State': "open",
                'CustomerUser': getattr(options, 'customer', os.environ.get("OTRS_CUSTOMER", "")),
                'Owner': getattr(options, 'owner', "root@localhost")
            },
            'Article': {
                'SenderType': "agent",
                'IsVisibleForCustomer': 1,
                'From': getattr(options, 'from_addr', "slack@yourdomain"),
                'To': getattr(options, 'to', os.environ.get("OTRS_CUSTOMER", "")),
                'Subject': options.title,
                'Body': body,
                'MimeType': "text/html",
                'Charset': "UTF-8",
                'TimeUnit': "0"
            },
            'DynamicField': getattr(options, 'dynamic_fields', [])
        }

        ticket = self.otrs_query(data, "TicketCreate")

        if (ticket.status_code == 500 and retry > 0):
            logger.critical(f"[Slack -> OTRS] Erro [500] na criação do ticket: {ticket.text} -- Tentando novamente")
            time.sleep(3)
            return self.create(options, retry-1)
        if (ticket.status_code != 200):
            logger.critical(f"[Slack -> OTRS] Erro [CODE: {ticket.status_code}] na criação do ticket: {ticket.text}")
            raise Exception(f"OTRS TicketCreate failed: {ticket.text}")
        ticket = ticket.json()
        logger.info(f"[Slack -> OTRS] Ticket Criado: {ticket['Ticket']['TicketNumber']}")
        return ticket

    def exists_by_dynamic_field(self, name, value, retry=2):
        data = {
            'SessionID': self.Token,
            'StateType': ['open', 'new', 'pending auto', 'pending reminder', 'Pendente com o Cliente'],
            'DynamicField': [
                {
                    'Name': name,
                    'Equals': value
                }
            ]
        }
        ticket = self.otrs_query(data, 'TicketSearch')
        if (ticket.status_code == 500 and retry > 0):
            time.sleep(3)
            return self.exists_by_dynamic_field(name, value, retry-1)
        if (ticket.status_code != 200 or 'ErrorCode' in ticket.text):
            logger.critical(f"[Slack -> OTRS] Erro ao verificar ticket: {ticket.text}")
            raise Exception(ticket.text)
        ticket = ticket.json()
        if ticket and ticket.get("TicketID"):
            return ticket["TicketID"][0]
        return False
