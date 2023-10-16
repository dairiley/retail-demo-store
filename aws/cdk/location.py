from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_apigatewayv2 as apigatewayv2,
    aws_dynamodb as dynamodb,
    aws_ec2 as ec2,
    aws_s3 as s3,
    CustomResource,
    RemovalPolicy
)
from constructs import Construct

class LocationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        location_resource_stack_lambda_role = iam.Role(self, "LocationResourceStackLambdaExecutionRole",
                                                       assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                       inline_policies={
                                                           "root": iam.PolicyDocument(statements=[
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "logs:CreateLogStream",
                                                                       "logs:PutLogEvents",
                                                                       "logs:CreateLogGroup"
                                                                   ],
                                                                   resources=["*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["s3:GetObject"],
                                                                   resources=[
                                                                       f"arn:aws:s3:::{props['resource_bucket']}",
                                                                       f"arn:aws:s3:::{props['resource_bucket']}/*"
                                                                   ]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "geo:AssociateTrackerConsumer",
                                                                       "geo:CreateTracker",
                                                                       "geo:DeleteTracker"
                                                                   ],
                                                                   resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:tracker*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "geo:PutGeofence",
                                                                       "geo:CreateGeofenceCollection",
                                                                       "geo:BatchDeleteGeofence",
                                                                       "geo:DeleteGeofenceCollection"
                                                                   ],
                                                                   resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:geofence-collection*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "geo:CreateMap",
                                                                       "geo:DeleteMap"
                                                                   ],
                                                                   resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:map*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "geo:CreatePlaceIndex",
                                                                       "geo:DeletePlaceIndex"
                                                                   ],
                                                                   resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:place-index*"]
                                                               )
                                                           ])
                                                       })

        location_resource_stack_function = lambda_.Function(self, "LocationResourceStackLambdaFunction",
                                                            runtime=lambda_.Runtime.PYTHON_3_10,
                                                            description="Function which manages the lifecycle (creation, update & deletion) of the Amazon Location resources used in the Location Service Demo",
                                                            function_name="LocationNrfDemoLocationResourceStack",
                                                            handler="location-resource-stack.lambda_handler",
                                                            code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LocationResourceStackLambdaFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/location-resource-stack.zip"),
                                                            timeout=Duration.seconds(900),
                                                            role=location_resource_stack_lambda_role,
                                                            environment={
                                                                "RESOURCE_BUCKET": props['resource_bucket'],
                                                                "RESOURCE_BUCKET_PATH": props['resource_bucket_relative_path']
                                                            })

        resource = CustomResource(self, "CustomLocationResourceStackLambdaFunction",
                                  service_token=location_resource_stack_function.function_arn,
                                  properties={"CreateDefaultGeofence": props['deploy_default_geofence']})
        self.location_resource_name = resource.get_att_string("LocationResourceName")

        location_geofence_event_log_group = logs.LogGroup(self, "LocationGeofenceEventLogGroup",
                                                          log_group_name=f"/aws/events/location-Monitor",
                                                          removal_policy=RemovalPolicy.DESTROY)

        websocket_connection_table = dynamodb.CfnTable(self, "WebSocketConnectionTable",
                                                       key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                           attribute_name="userId",
                                                           key_type="HASH"
                                                       )],
                                                       attribute_definitions=[dynamodb.CfnTable.AttributeDefinitionProperty(
                                                           attribute_name="userId",
                                                           attribute_type="S"
                                                       )],
                                                       billing_mode="PAY_PER_REQUEST")

        """
        API Gateway & associated resources to support browser notifications via WebSockets
        """

        location_geofence_browser_notification_api = apigatewayv2.CfnApi(self, "LocationGeofenceBrowserNotificationApi",
                                                                         protocol_type="WEBSOCKET",
                                                                         name="LocationNrfDemo",
                                                                         route_selection_expression="$request.body.action")

        api_deployment = apigatewayv2.CfnDeployment(self, "LocationGeofenceBrowserNotificationApiDeployment",
                                                    api_id=location_geofence_browser_notification_api.attr_api_id)

        location_geofence_browser_notification_api_stage = apigatewayv2.CfnStage(self, "LocationGeofenceBrowserNotificationApiStage",
                                                                                 stage_name="Prod",
                                                                                 deployment_id=api_deployment.attr_deployment_id,
                                                                                 api_id=location_geofence_browser_notification_api.attr_api_id)

        location_geofence_event_handler_role = iam.Role(self, "LocationGeofenceEventHandlerLambdaExecutionRole",
                                                        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                        managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "LocationGeofenceEventHandlerLambdaExecutionRoleVPCAccess",
                                                                                                                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")],
                                                        inline_policies={
                                                           "root": iam.PolicyDocument(statements=[
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "logs:CreateLogStream",
                                                                       "logs:PutLogEvents",
                                                                       "logs:CreateLogGroup"
                                                                   ],
                                                                   resources=["*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["cognito-idp:AdminGetUser"],
                                                                   resources=[f"arn:aws:cognito-idp:{Aws.REGION}:{Aws.ACCOUNT_ID}:userpool/{props['user_pool_id']}"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["mobiletargeting:SendMessages"],
                                                                   resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/props['pinpoint_app_id']/messages"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["mobiletargeting:GetUserEndpoints"],
                                                                   resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/users/*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["mobiletargeting:UpdateEndpoint"],
                                                                   resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/endpoints/*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["mobiletargeting:PutEvents"],
                                                                   resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/events"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "dynamodb:GetItem",
                                                                       "dynamodb:UpdateItem",
                                                                       "dynamodb:DeleteItem"
                                                                   ],
                                                                   resources=[websocket_connection_table.attr_arn]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["execute-api:ManageConnections"],
                                                                   resources=[f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{location_geofence_browser_notification_api}/*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["ssm:GetParameter"],
                                                                   resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore-pinpoint-sms-longcode"]
                                                               )
                                                           ])
                                                        })

        location_geofence_event_handler_function = lambda_.Function(self, "LocationGeofenceEventHandler",
                                                                    runtime=lambda_.Runtime.PYTHON_3_10,
                                                                    description="Handles Amazon Location geofence entry/exit events in Location Service demo",
                                                                    function_name="LocationNrfDemoGeofenceEventHandler",
                                                                    handler="location-resource-stack.lambda_handler",
                                                                    code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LocationGeofenceEventHandlerBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/location-geofence-event.zip"),
                                                                    timeout=Duration.seconds(900),
                                                                    role=location_geofence_event_handler_role,
                                                                    vpc=props['vpc'],
                                                                    allow_public_subnet=True,
                                                                    vpc_subnets=ec2.SubnetSelection(subnets=[props['private_subnet1'], props['private_subnet2']]),
                                                                    environment={
                                                                        "UserPoolId": props['user_pool_id'],
                                                                        "PinpointAppId": props['pinpoint_app_id'],
                                                                        "EmailFromAddress": props['pinpoint_email_from_address'],
                                                                        "ProductsServiceExternalUrl": props['products_service_external_url'],
                                                                        "CartsServiceExternalUrl": props['carts_service_external_url'],
                                                                        "OrdersServiceExternalUrl": props['orders_service_external_url'],
                                                                        "OffersServiceExternalUrl": props['offers_service_external_url'],
                                                                        "UsersServiceExternalUrl": props['users_service_external_url'],
                                                                        "WebURL": props['web_url'],
                                                                        "NotificationEndpointUrl": f"{location_geofence_browser_notification_api.attr_api_endpoint}/{location_geofence_browser_notification_api_stage}",
                                                                        "WebsocketDynamoTableName": websocket_connection_table.ref
                                                                    })

        location_geofence_event_rule = events.Rule(self, "LocationGeofenceEventRule",
                                                   description="Rule for Location Service demo to trigger when devices enter/exit a geofence",
                                                   event_pattern=events.EventPattern(
                                                       source=["aws.geo"],
                                                       detail={
                                                           "EventType": ["ENTER"]
                                                       },
                                                       detail_type=["Location Geofence Event"],
                                                       resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:geofence-collection/location"]
                                                   ))
        location_geofence_event_rule.add_target(targets.LambdaFunction(location_geofence_event_handler_function))
        location_geofence_event_rule.add_target(targets.CloudWatchLogGroup(location_geofence_event_log_group))

        location_geofence_event_handler_function.add_permission("LocationGeofenceEventRuleInvokeLambdaPermission",
                                                               principal=iam.ServicePrincipal("events.amazonaws.com"),
                                                               source_arn=location_geofence_event_rule.rule_arn)

        lambda_.EventInvokeConfig(self, "LocationGeofenceEventHandlerEventConfig",
                                  function=location_geofence_event_handler_function,
                                  retry_attempts=0)

        location_geofence_websocket_lambda_role = iam.Role(self, "LocationGeofenceWebsocketConnectLambdaExecutionRole",
                                                           assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                           inline_policies={
                                                               "root": iam.PolicyDocument(statements=[
                                                                   iam.PolicyStatement(
                                                                       actions=[
                                                                           "logs:CreateLogStream",
                                                                           "logs:PutLogEvents",
                                                                           "logs:CreateLogGroup"
                                                                       ],
                                                                       resources=["*"]
                                                                   ),
                                                                   iam.PolicyStatement(
                                                                       actions=[
                                                                           "dynamodb:GetItem",
                                                                           "dynamodb:UpdateItem",
                                                                           "dynamodb:PutItem"
                                                                       ],
                                                                       resources=[websocket_connection_table.attr_arn]
                                                                   )
                                                               ])
                                                           })

        location_geofence_websocket_connect_lambda = lambda_.Function(self, "LocationGeofenceWebsocketConnectLambda",
                                                                      runtime=lambda_.Runtime.PYTHON_3_10,
                                                                      description="Handles connections to the WebSocket API processing Location Geofence notifications",
                                                                      function_name="LocationNrfDemoNotificationApiConnect",
                                                                      handler="websocket-connect.lambda_handler",
                                                                      code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LocationGeofenceWebsocketConnectLambdaBucket", bucket_name=props['resource_bucket']),
                                                                                                    f"{props['resource_bucket_relative_path']}aws-lambda/websocket-connect.zip"),
                                                                      timeout=Duration.seconds(30),
                                                                      role=location_geofence_websocket_lambda_role,
                                                                      environment={
                                                                          "WebsocketDynamoTableName": websocket_connection_table.ref})
        location_geofence_websocket_connect_lambda.add_permission("ConnectionLambdaInvokePermission",
                                                                  principal=iam.ServicePrincipal(
                                                                      "apigateway.amazonaws.com"))

        location_geofence_websocket_disconnect_lambda = lambda_.Function(self, "LocationGeofenceWebsocketDisconnectLambda",
                                                                         runtime=lambda_.Runtime.PYTHON_3_10,
                                                                         description="Handles disconnection from the WebSocket API processing Location Geofence notifications",
                                                                         function_name="LocationNrfDemoNotificationApiDisconnect",
                                                                         handler="websocket-disconnect.lambda_handler",
                                                                         code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LocationGeofenceWebsocketDisconnectLambdaBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/websocket-disconnect.zip"),
                                                                         timeout=Duration.seconds(30),
                                                                         role=location_geofence_websocket_lambda_role,
                                                                         environment={"WebsocketDynamoTableName": websocket_connection_table.ref})
        location_geofence_websocket_disconnect_lambda.add_permission("ConnectionLambdaInvokePermission",
                                                                     principal=iam.ServicePrincipal("apigateway.amazonaws.com"))

        lambda_authorizer_role = iam.Role(self, "LambdaAuthorizerRole",
                                          assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                          managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "LambdaAuthorizerRoleBasicExecutionRole",
                                                                                                      managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")])

        lambda_authorizer_function = lambda_.Function(self, "LambdaAuthorizerFunction",
                                                      runtime=lambda_.Runtime.NODEJS_18_X,
                                                      handler="index.handler",
                                                      code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LambdaAuthorizerFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/apigw-ws-authorizer.zip"),
                                                      timeout=Duration.seconds(60),
                                                      role=lambda_authorizer_role,
                                                      memory_size=512,
                                                      environment={"ALLOWED_ORIGIN": props['web_url']})

        lambda_authorizer = apigatewayv2.CfnAuthorizer(self, "LambdaAuthorizer",
                                                       name="LambdaAuthorizer",
                                                       api_id=location_geofence_browser_notification_api.attr_api_id,
                                                       authorizer_type="REQUEST",
                                                       authorizer_uri=f"arn:aws:apigateway:{Aws.REGION}:lambda:path/2015-03-31/functions/{lambda_authorizer_function.function_arn}/invocations")

        lambda_authorizer_function.add_permission("LambdaAuthorizerFunctionPermission",
                                                  principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
                                                  source_arn=f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{location_geofence_browser_notification_api.attr_api_id}/authorizers/{lambda_authorizer.attr_authorizer_id}")

        location_geofence_websocket_connection_integration = apigatewayv2.CfnIntegration(self, "LocationGeofenceWebsocketConnectionIntegration",
                                                                                         api_id=location_geofence_browser_notification_api.attr_api_id,
                                                                                         integration_type="AWS_PROXY",
                                                                                         integration_uri=f"arn:aws:apigateway:{Aws.REGION}:lambda:path/2015-03-31/functions/{location_geofence_websocket_connect_lambda.function_arn}/invocations")
        location_geofence_browser_notification_api_connect_route = apigatewayv2.CfnRoute(self, "LocationGeofenceBrowserNotificationApiConnectRoute",
                                                                                         api_id=location_geofence_browser_notification_api.attr_api_id,
                                                                                         route_key="$connect",
                                                                                         authorization_type="CUSTOM",
                                                                                         authorizer_id=lambda_authorizer.attr_authorizer_id,
                                                                                         operation_name="ConnectRoute",
                                                                                         target=f"integrations/{location_geofence_websocket_connection_integration.ref}")

        location_geofence_websocket_disconnect_integration = apigatewayv2.CfnIntegration(self, "LocationGeofenceWebsocketDisconnectIntegration",
                                                                                         api_id=location_geofence_browser_notification_api.attr_api_id,
                                                                                         integration_type="AWS_PROXY",
                                                                                         integration_uri=f"arn:aws:apigateway:{Aws.REGION}:lambda:path/2015-03-31/functions/{location_geofence_websocket_disconnect_lambda.function_arn}/invocations")
        location_geofence_browser_notification_api_disconnect_route = apigatewayv2.CfnRoute(self, "LocationGeofenceBrowserNotificationApiDisconnectRoute",
                                                                                         api_id=location_geofence_browser_notification_api.attr_api_id,
                                                                                         route_key="$disconnect",
                                                                                         operation_name="DisconnectRoute",
                                                                                         target=f"integrations/{location_geofence_websocket_disconnect_integration.ref}")

        api_deployment.add_dependency(location_geofence_browser_notification_api_connect_route)
        api_deployment.add_dependency(location_geofence_browser_notification_api_disconnect_route)

        self.location_notification_endpoint = f"{location_geofence_browser_notification_api.attr_api_endpoint}/{location_geofence_browser_notification_api_stage.ref}"
