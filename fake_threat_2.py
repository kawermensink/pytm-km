#!/usr/bin/env python3

from pytm.pytm import TM, Server, Data, Datastore, Dataflow, Boundary, Actor, Process, Lambda, ExternalEntity, Classification

tm = TM("Fake Aps")
tm.description = "Fake Aps billing service"
tm.isOrdered = True

#Boundary
Client_web = Boundary("Client/Web")
Web_production = Boundary("Web/Production")

#Actor
client = Actor("Client")
client.inBoundary = Client_web
client.protocol = "HTTPS"

#Trust boundary
web = Server("Production")
web.OS = "Unix"
web.isHardened = True

#Datastores
billing_db = Datastore("SQL Database (*)")
billing_db.inBoundary = Web_production
billing_db.isSQL = True
billing_db.inScope = True
billing_db.storesSensitiveData = True

logs_db = Datastore("AWS_S3 Database (*)")
logs_db.inBoundary = Web_production
logs_db.inScope = True

#Processes
process_gateway = Process("web/gateway")
process_gateway.inScope = True

process_billing_service = Process("web/billing_service")
process_billing_service.inScope = True

#External entities
external_visa = ExternalEntity("VISA")
external_visa.inScope = False

#data
update_payment = Data(
	name="Update payment",
	description="Transaction data",
	classificaion= Classification.SENSITIVE,
	isPII=True,
	isStored=True,
	isSourceEncryptedAtRest=True,
	isDestEncryptedAtRest=False,
	
)

billing_update = Data(
	name="Billing update",
	description="billing data updated",
	classificaion= Classification.SENSITIVE,
	isPII=True,
	isStored=True,
	isSourceEncryptedAtRest=True,
	isDestEncryptedAtRest=True
)

credit_card_check = Data(
	name="Credit card auth",
	description="Verification of credit card transaction by user",
	classificaion= Classification.SENSITIVE,
	isPII=True,
	isStored=False,
	isSourceEncryptedAtRest=True,
	isDestEncryptedAtRest=True
)

audit_log = Data(
	name="Audit log",
	description="Logging of billing payment",
	classificaion= Classification.SENSITIVE,
	isPII=False,
	isStored=True,
	isSourceEncryptedAtRest=True,
	isDestEncryptedAtRest=True
)

#Dataflows
##internal
client_to_web = Dataflow(client, process_gateway, "Client updates payment")
client_to_web.protocol = "HTTPS"
client_to_web.dstPort = 443
client_to_web.data = update_payment

gateway_api_to_billing_service = Dataflow(process_gateway, process_billing_service, "Billing data stored")
gateway_api_to_billing_service.protocol = "HTTP"
gateway_api_to_billing_service.dstPort = 80
gateway_api_to_billing_service.data = update_payment

billing_service_to_billing_db = Dataflow(process_billing_service, billing_db, "Insert billing data")
billing_service_to_billing_db.protocol = "MySQL"
billing_service_to_billing_db.dstPort = 3306
billing_service_to_billing_db.data = billing_update

billing_service_to_logs = Dataflow(process_billing_service, logs_db, "Payment status")
billing_service_to_logs.protocol = "HTTPS"
billing_service_to_logs.dstPort = 443
billing_service_to_logs.data = audit_log

##external
external_visa_to_billing_service = Dataflow(external_visa, process_billing_service, "auth")
external_visa_to_billing_service.protocol = "HTTPS"
external_visa_to_billing_service.dstPort = 443
external_visa_to_billing_service.data = audit_log

billing_service_to_external_visa = Dataflow(process_billing_service, external_visa, "auth")
billing_service_to_external_visa.protocol = "HTTPS"
billing_service_to_external_visa.dstPort = 443
billing_service_to_external_visa.data = audit_log

#Lambda
aws_lambda = Lambda("logBilligDataEvery6hours")
aws_lambda.onAWS = True
aws_lambda.hasAccessControl = True

'''
billing_data = Data(
	name="billing data",
	classificaion=Classification.SENSITIVE,
	isPII=True,
	isCredentials=False,
	isStored=True,n
	isSourceEncryptedAtRest=True,
	isDestEncryptedAtRest=True
)

billing_logs = Data(
	name="billing logs",
	classification=Classification.SENSITIVE,
	isPII=False,
	isCredentials=True,
	isStored=True,
	isSourceEncryptedAtRest=True,
	isDestEncryptedAtRest=False
)

my_lambda = Lambda("logBilligDataEvery6hours")
my_lambda.hasAccessControl = True
my_lambda.inBoundary = Web_DB

user_to_web = Dataflow(client, web, "Client updates payment")
user_to_web.protocol = "HTTPS"
user_to_web.dstPort = 443
user_to_web.data = "billing data"

web_to_user = Dataflow(web, client, "Billing data stored")
web_to_user.protocol = "HTTPS"
web_to_user.data = "ACK of saving or error message, in JSON format"

web_to_db = Dataflow(web, db, "Insert billing data")
web_to_db.protocol = "MySQL"
web_to_db.dstPort = 3306
web_to_db.data = "MySQL insert statement, all literals"

db_to_web = Dataflow(db, web, "Payment success")
db_to_web.protocol = "MySQL"
db_to_web.data = "Confirmation/rejection of payment"
'''
tm.process()
