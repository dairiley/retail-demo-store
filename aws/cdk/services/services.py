from .pinpoint_personalize import PinpointPersonalizeStack
from .products_custom import ProductsCustomStack
from .service.serviceapp import ServiceAppStack
from constructs import Construct
from aws_cdk import Stack, Aws, aws_iam as iam, aws_lambda as lambda_, aws_logs as logs, Duration, BundlingOptions, RemovalPolicy

class ServicesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        container_memory="512"
        container_cpu="256"
        container_image="amazon/amazon-ecs-sample"

        delete_repository_lambda_role = iam.Role(self, "DeleteRepositoryLambdaExecutionRole",
                                                 assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                 inline_policies={
                                                     "root": iam.PolicyDocument(statements=[
                                                         iam.PolicyStatement(
                                                             actions=[
                                                                 "logs:CreateLogStream",
                                                                 "logs:PutLogEvents",
                                                                 "logs:CreateLogGroup",
                                                             ],
                                                             resources=["*"]
                                                         ),
                                                         iam.PolicyStatement(
                                                             actions=["ecr:DeleteRepository"],
                                                             resources=[f"arn:aws:ecr:{Aws.REGION}:{Aws.ACCOUNT_ID}:repository/retaildemostore*"]
                                                         )
                                                     ])
                                                 })

        delete_repository_lambda = lambda_.Function(self, "DeleteRepositoryLambdaFunction",
                                                    runtime=lambda_.Runtime.PYTHON_3_7,
                                                    description="Retail Demo Store deployment utility function that deletes an Amazon ECR repository when the CloudFormation stack is deleted",
                                                    handler="index.handler",
                                                    code=lambda_.Code.from_asset("services/lambda/delete_repository",
                                                                                 bundling=BundlingOptions(
                                                                                     image=lambda_.Runtime.PYTHON_3_7.bundling_image,
                                                                                     command=[
                                                                                         "bash", "-c",
                                                                                         "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                                                                                     ],
                                                                                 )),
                                                    timeout=Duration.seconds(30),
                                                    role=delete_repository_lambda_role)

        log_group = logs.LogGroup(self, "LogGroup",
                                  log_group_name=f"/ecs/{props['stack_name']}",
                                  removal_policy=RemovalPolicy.DESTROY)

        service_props = {
            "service_name": "",
            "service_path": "",
            "stack_name": props['stack_name'],
            "resource_bucket": props['resource_bucket'],
            "source_deployment_type": props['source_deployment_type'],
            "github_repo": props['github_repo'],
            "github_branch": props['github_branch'],
            "github_token": props['github_token'],
            "github_user": props['github_user'],
            "user_pool_id": props['user_pool_id'],
            "user_pool_client_id": props['user_pool_client_id'],
            "identity_pool_id": props['identity_pool_id'],
            "subnet1": props['private_subnet1'],
            "subnet2": props['private_subnet2'],
            "vpc": props['vpc'],
            "vpc_cidr": props['vpc_cidr'],
            "container_memory": container_memory,
            "container_cpu": container_cpu,
            "container_image": container_image,
            "cluster": props['cluster'],
            "service_discovery_namespace": props['service_discovery_namespace'],
            "products_table": props['products_table'],
            "categories_table": props['categories_table'],
            "experiment_strategy_table": props['experiment_strategy_table'],
            "parameter_personalize_event_tracker_id": props['parameter_personalize_event_tracker_id'],
            "parameter_amplitude_api_key": props['parameter_amplitude_api_key'],
            "parameter_optimizely_sdk_key": props['parameter_optimizely_sdk_key'],
            "amazon_pay_signing_lambda": props['amazon_pay_signing_lambda'],
            "delete_repository_lambda": delete_repository_lambda,
            "web_root_url": props['web_root_url'],
            "image_root_url": props['image_root_url'],
            "evidently_project_name": props['evidently_project_name'],
            "parameter_ivs_video_channel_map": props['parameter_ivs_video_channel_map'],
            "pinpoint_app_id": props['pinpoint_app_id'],
            "opensearch_domain_endpoint": props['opensearch_domain_endpoint'],
            "cleanup_bucket_lambda_arn": props['cleanup_bucket_lambda_arn'],
            "log_group": log_group,
            "logging_bucket": props['logging_bucket'],
        }

        products_props = service_props
        products_props['service_name'] = "products"
        products_props['service_path'] = "src/products"
        self.products = ServiceAppStack(self, "ProductsService",
                                        props=products_props)
        self.add_dependency(self.products)

        users_props = service_props
        users_props['service_name'] = "users"
        users_props['service_path'] = "src/users"
        self.users = ServiceAppStack(self, "UsersService",
                                     props=users_props)
        self.add_dependency(self.users)

        carts_props = service_props
        carts_props['service_name'] = "carts"
        carts_props['service_path'] = "src/carts"
        self.carts = ServiceAppStack(self, "CartsService",
                                     props=carts_props)
        self.add_dependency(self.carts)

        orders_props = service_props
        orders_props['service_name'] = "orders"
        orders_props['service_path'] = "src/orders"
        self.orders = ServiceAppStack(self, "OrdersService",
                                      props=orders_props)
        self.add_dependency(self.orders)

        search_props = service_props
        search_props['service_name'] = "search"
        search_props['service_path'] = "src/search"
        self.search = ServiceAppStack(self, "SearchService",
                                      props=search_props)
        self.add_dependency(self.search)

        location_props = service_props
        location_props['service_name'] = "location"
        location_props['service_path'] = "src/location"
        self.location = ServiceAppStack(self, "LocationService",
                                        props=location_props)
        self.add_dependency(self.location)

        offers_props = service_props
        offers_props['service_name'] = "offers"
        offers_props['service_path'] = "src/offers"
        self.offers = ServiceAppStack(self, "OffersService",
                                      props=offers_props)

        recommendations_props = service_props
        recommendations_props['service_name'] = "recommendations"
        recommendations_props['service_path'] = "src/recommendations"
        self.recommendations = ServiceAppStack(self, "RecommendationsService",
                                               props=recommendations_props)
        self.add_dependency(self.recommendations)

        videos_props = service_props
        videos_props['service_name'] = "videos"
        videos_props['service_path'] = "src/videos"
        self.videos = ServiceAppStack(self, "VideosService",
                                      props=videos_props)
        self.add_dependency(self.videos)

        pinpoint_personalize_props = {
            "pinpoint_app_id": props['pinpoint_app_id'],
            "resource_bucket": props['resource_bucket'],
            "resource_bucket_relative_path": props['resource_bucket_relative_path'],
            "recommendations_service_dns_name": self.recommendations.load_balancer.load_balancer.attr_dns_name,
            "offers_service_dns_name": self.offers.load_balancer.load_balancer.attr_dns_name,
            "products_service_dns_name": self.products.load_balancer.load_balancer.attr_dns_name,
            "vpc": props['vpc'],
            "private_subnet1": props['private_subnet1'],
            "private_subnet2": props['private_subnet2'],
            "uid": f"{props['stack_name']}-{Aws.REGION}"}
        self.pinpoint_personalize = PinpointPersonalizeStack(self, "PinpointPersonalize",
                                                             props=pinpoint_personalize_props)

        custom_resources_props = {
            "products_table": props['products_table'],
            "categories_table": props['categories_table'],
            "resource_bucket": props['resource_bucket'],
            "resource_bucket_relative_path": props['resource_bucket_relative_path']
        }
        ProductsCustomStack(self, "CustomResources",
                            props=custom_resources_props)
