#!/usr/bin/env python3

from pytm.pytm import TM, Server, Data, Datastore, Dataflow, Boundary, Actor, Process, Lambda, ExternalEntity, Classification

tm = TM("Fake Aps")
tm.description = "Fake Aps billing service"
tm.isOrdered = True

#Trust boundary
production = Boundary("Production")

#Actor
client = Actor("Client")
client.protocol = "HTTPS"

#Datastores
billing_db = Datastore("SQL Database (*)")
billing_db.inBoundary = production
billing_db.isSQL = True
billing_db.inScope = True
billing_db.storesSensitiveData = True

logs_db = Datastore("AWS_S3 Database (*)")
logs_db.inBoundary = production
logs_db.inScope = True

#Processes
process_gateway = Process("gateway API")
process_gateway.inScope = True
process_gateway.inBoundary = production

process_billing_service = Process("Billing service")
process_billing_service.inScope = True
process_billing_service.inBoundary = production

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
	isDestEncryptedAtRest=False
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
external_visa_to_billing_service = Dataflow(external_visa, process_billing_service, "authorization")
external_visa_to_billing_service.protocol = "HTTPS"
external_visa_to_billing_service.dstPort = 443
external_visa_to_billing_service.data = credit_card_check

billing_service_to_external_visa = Dataflow(process_billing_service, external_visa, "authentication")
billing_service_to_external_visa.protocol = "HTTPS"
billing_service_to_external_visa.dstPort = 443
billing_service_to_external_visa.data = credit_card_check

'''
#Lambda
aws_lambda = Lambda("logBilligDataEvery6hours")
aws_lambda.onAWS = True
aws_lambda.hasAccessControl = True
'''

tm.process()
