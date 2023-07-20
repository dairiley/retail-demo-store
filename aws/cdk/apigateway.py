from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_apigatewayv2 as apigatewayv2,
    aws_logs as logs
)
from constructs import Construct

class ApiGatewayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_authorizer_role = iam.Role(self, "LambdaAuthorizerRole",
                                          assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                          managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "LambdaAuthorizerRoleVPCAccess",
                                                                                                               managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")])

        lambda_authorizer_function = lambda_.Function(self, "LambdaAuthorizerFunction",
                                                      runtime=lambda_.Runtime.NODEJS_18_X,
                                                      handler="index.handler",
                                                      code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LambdaAuthorizerFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/apigw-authorizer.zip"),
                                                      timeout=Duration.seconds(60),
                                                      role=lambda_authorizer_role,
                                                      memory_size=512,
                                                      environment={
                                                          "USER_POOL_ID": props['user_pool_id'],
                                                          "CLIENT_ID": props['user_pool_client_id']
                                                      })

        security_group = ec2.SecurityGroup(self, "VpcLinkSecurityGroup",
                                           vpc=props['vpc'],
                                           description=f"{props['stack_name']}/VPCLinkSecurityGroup")
        security_group.add_ingress_rule(ec2.Peer.ipv4(props['cidr']), ec2.Port.tcp(80), "Allow from within the VPC for port 80")

        vpc_link = apigatewayv2.CfnVpcLink(self, "VpcLink",
                                           name=f"{props['stack_name']}-VPCLink",
                                           subnet_ids=[],#@todo
                                           security_group_ids=["securityGroupIds"])#@todo

        self.http_api = apigatewayv2.CfnApi(self, "HttpAPI",
                                            name=f"{props['stack_name']}-APIGateway",
                                            protocol_type="HTTP",
                                            cors_configuration=apigatewayv2.CfnApi.CorsProperty(
                                                allow_credentials=False,
                                                allow_headers=["accept", "accept-encoding", "authorization", "content-length",
                                                               "content-type", "x-csrff-token"],
                                                allow_methods=["GET", "OPTIONS", "POST", "PUT"],
                                                allow_origins=["*"],
                                                expose_headers=["*"],
                                                max_age=600
                                            ))

        lambda_authorizer = apigatewayv2.CfnAuthorizer(self, "LambdaAuthorizer",
                                                    api_id=self.http_api.attr_api_id,
                                                    authorizer_type="REQUEST",
                                                    authorizer_payload_format_version="2.0",
                                                    name="LambdaAuthorizer",
                                                    authorizer_uri=f"arn:aws:apigateway:{Aws.REGION}:lambda:path/2015-03-31/functions/{lambda_authorizer_function.function_arn}/invocations",
                                                    enable_simple_responses=True)

        lambda_authorizer_function.add_permission("LambdaAuthorizerFunctionPermission",
                                                  principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
                                                  source_arn=f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{self.http_api.attr_api_id}/authorizers/{lambda_authorizer.ref}")

        products_service_integration = apigatewayv2.CfnIntegration(self, "ProductsServiceIntegration",
                                                                   api_id=self.http_api.attr_api_id,
                                                                   description="Product Service Integration",
                                                                   connection_type="VPC_LINK",
                                                                   connection_id=vpc_link.ref,
                                                                   integration_type="HTTP_PROXY",
                                                                   integration_method="ANY",
                                                                   integration_uri=props['products_service_elb_listener'].attr_listener_arn,
                                                                   passthrough_behavior="WHEN_NO_MATCH",
                                                                   payload_format_version="1.0")

        users_service_integration = apigatewayv2.CfnIntegration(self, "UsersServiceIntegration",
                                                                api_id=self.http_api.attr_api_id,
                                                                description="Users Service Integration",
                                                                connection_type="VPC_LINK",
                                                                connection_id=vpc_link.ref,
                                                                integration_type="HTTP_PROXY",
                                                                integration_method="ANY",
                                                                integration_uri=props['users_service_elb_listener'].attr_listener_arn,
                                                                passthrough_behavior="WHEN_NO_MATCH",
                                                                payload_format_version="1.0")

        carts_service_integration = apigatewayv2.CfnIntegration(self, "CartsServiceIntegration",
                                                                api_id=self.http_api.attr_api_id,
                                                                description="Carts Service Integration",
                                                                connection_type="VPC_LINK",
                                                                connection_id=vpc_link.ref,
                                                                integration_type="HTTP_PROXY",
                                                                integration_method="ANY",
                                                                integration_uri=props['carts_service_elb_listener'].attr_listener_arn,
                                                                passthrough_behavior="WHEN_NO_MATCH",
                                                                payload_format_version="1.0")

        orders_service_integration = apigatewayv2.CfnIntegration(self, "OrdersServiceIntegration",
                                                                 api_id=self.http_api.attr_api_id,
                                                                 description="Orders Service Integration",
                                                                 connection_type="VPC_LINK",
                                                                 connection_id=vpc_link.ref,
                                                                 integration_type="HTTP_PROXY",
                                                                 integration_method="ANY",
                                                                 integration_uri=props['orders_service_elb_listener'].attr_listener_arn,
                                                                 passthrough_behavior="WHEN_NO_MATCH",
                                                                 payload_format_version="1.0")

        recommendations_service_integration = apigatewayv2.CfnIntegration(self, "RecommendationsServiceIntegration",
                                                                          api_id=self.http_api.attr_api_id,
                                                                          description="Recommendations Service Integration",
                                                                          connection_type="VPC_LINK",
                                                                          connection_id=vpc_link.ref,
                                                                          integration_type="HTTP_PROXY",
                                                                          integration_method="ANY",
                                                                          integration_uri=props['recommendations_service_elb_listener'].attr_listener_arn,
                                                                          passthrough_behavior="WHEN_NO_MATCH",
                                                                          payload_format_version="1.0")

        videos_service_integration = apigatewayv2.CfnIntegration(self, "VideosServiceIntegration",
                                                                 api_id=self.http_api.attr_api_id,
                                                                 description="Videos Service Integration",
                                                                 connection_type="VPC_LINK",
                                                                 connection_id=vpc_link.ref,
                                                                 integration_type="HTTP_PROXY",
                                                                 integration_method="ANY",
                                                                 integration_uri=props['videos_service_elb_listener'].attr_listener_arn,
                                                                 passthrough_behavior="WHEN_NO_MATCH",
                                                                 payload_format_version="1.0")

        search_service_integration = apigatewayv2.CfnIntegration(self, "SearchServiceIntegration",
                                                                 api_id=self.http_api.attr_api_id,
                                                                 description="Search Service Integration",
                                                                 connection_type="VPC_LINK",
                                                                 connection_id=vpc_link.ref,
                                                                 integration_type="HTTP_PROXY",
                                                                 integration_method="ANY",
                                                                 integration_uri=props['search_service_elb_listener'].attr_listener_arn,
                                                                 passthrough_behavior="WHEN_NO_MATCH",
                                                                 payload_format_version="1.0")

        location_service_integration = apigatewayv2.CfnIntegration(self, "LocationServiceIntegration",
                                                                   api_id=self.http_api.attr_api_id,
                                                                   description="Locaiton Service Integration",
                                                                   connection_type="VPC_LINK",
                                                                   connection_id=vpc_link.ref,
                                                                   integration_type="HTTP_PROXY",
                                                                   integration_method="ANY",
                                                                   integration_uri=props['location_service_elb_listener'].attr_listener_arn,
                                                                   passthrough_behavior="WHEN_NO_MATCH",
                                                                   payload_format_version="1.0")

        get_product = apigatewayv2.CfnRoute(self, "GetProduct",
                                            api_id=self.http_api.attr_api_id,
                                            route_key="GET /products/id/{id}",
                                            authorization_type="CUSTOM",
                                            authorizer_id=lambda_authorizer.ref,
                                            target=f"integrations/{products_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCategory",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /products/category/{name}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{products_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetFeatured",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /products/featured",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{products_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCategories",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /categories/all",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{products_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "CreateUser",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /users",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetUserById",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /users/id/{id}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "UpdateUser",
                              api_id=self.http_api.attr_api_id,
                              route_key="PUT /users/id/{id}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetUserByUsername",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /users/username/{username}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetUnclaimedUser",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /users/unclaimed",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetRandomUser",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /users/random",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "ClaimUser",
                              api_id=self.http_api.attr_api_id,
                              route_key="PUT /users/id/{userId}/claim",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "VerifyPhone",
                              api_id=self.http_api.attr_api_id,
                              route_key="PUT /users/id/{userId}/verifyphone",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{users_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "CreateCart",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /carts",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{carts_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCart",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /carts/{cartId}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{carts_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "UpdateCart",
                              api_id=self.http_api.attr_api_id,
                              route_key="PUT /carts/{cartId}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{carts_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "Sign",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /sign",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{carts_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "CreateOrder",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /orders",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{orders_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetOrders",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /orders/all",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{orders_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetOrderById",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /orders/id/{orderId}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{orders_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetOrderByUsername",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /orders/username/{username}",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{orders_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetRecommendations",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /recommendations",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetPopular",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /popular",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetRelated",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /related",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "Rerank",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /rerank",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetDiscounts",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /choose_discounted",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCouponOffer",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /coupon_offer",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "RecordExperimentOutcome",
                              api_id=self.http_api.attr_api_id,
                              route_key="POST /experiment/outcome",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{recommendations_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "VideoStream",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /stream_details",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{videos_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "SearchProducts",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /search/products",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{search_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetStoreLocation",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /store_location",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{location_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCustomerRoute",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /customer_route",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{location_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCStoreLocation",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /cstore_location",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{location_service_integration.ref}")

        apigatewayv2.CfnRoute(self, "GetCStoreRoute",
                              api_id=self.http_api.attr_api_id,
                              route_key="GET /cstore_route",
                              authorization_type="CUSTOM",
                              authorizer_id=lambda_authorizer.ref,
                              target=f"integrations/{location_service_integration.ref}")

        access_logs = logs.LogGroup(self, "AccessLogs",
                                    log_group_name=f"{props['stack_name']}/APIAccessLogs",
                                    retention=logs.RetentionDays.ONE_MONTH)

        http_api_stage = apigatewayv2.CfnStage(self, "HttpApiStage",
                                               stage_name="$default",
                                               api_id=self.http_api.attr_api_id,
                                               auto_deploy=True,
                                               access_log_settings=apigatewayv2.CfnStage.AccessLogSettingsProperty(
                                                   destination_arn=access_logs.log_group_arn,
                                                   format='{ "requestId":"$context.requestId", "ip": "$context.identity.sourceIp", "requestTime":"$context.requestTime", "httpMethod":"$context.httpMethod","routeKey":"$context.routeKey", "status":"$context.status","protocol":"$context.protocol", "integrationStatus": $context.integrationStatus, "integrationLatency": $context.integrationLatency, "responseLength":"$context.responseLength", "authorizerError": "$context.authorizer.error" }'
                                               ))
        http_api_stage.add_dependency(get_product)
