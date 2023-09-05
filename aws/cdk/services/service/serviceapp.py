from .loadbalancer import LoadBalancerStack
from .pipeline import PipelineStack
from .service import ServiceStack
from constructs import Construct
from aws_cdk import Stack, Aws

class ServiceAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_balancer_props = {
            "service_name": props['service_name'],
            "subnet1": props['subnet1'],
            "subnet2": props['subnet2'],
            "vpc": props['vpc'],
            "cidr": props['vpc_cidr'],
            "stack_name": props['stack_name']
        }
        self.load_balancer = LoadBalancerStack(self, "LoadBalancer",
                                               props=load_balancer_props)

        service_props = {
            "service_name": props['service_name'],
            "products_table": props['products_table'],
            "categories_table": props['categories_table'],
            "experiment_strategy_table": props['experiment_strategy_table'],
            "resource_bucket": props['resource_bucket'],
            "amazon_pay_signing_lambda": props['amazon_pay_signing_lambda'],
            "evidently_project_arn": f"arn:aws:evidently:{Aws.REGION}:{Aws.ACCOUNT_ID}:project/{props['evidently_project_name']}",
            "evidently_project_name": props['evidently_project_name'],
            "container_memory": props['container_memory'],
            "container_cpu": props['container_cpu'],
            "container_image": props['container_image'],
            "env_personalize_campaign_arn": "",
            "env_personalize_search_campaign_arn": "",
            "env_products_service_internal_url": "products.retaildemostore.local",
            "env_users_service_internal_url": "users.retaildemostore.local",
            "env_search_service_internal_url": "search.retaildemostore.local",
            "env_offers_service_internal_url": "offers.retaildemostore.local",
            "parameter_ivs_video_channel_map": props['parameter_ivs_video_channel_map'],
            "use_default_ivs_streams": False,
            "env_opensearch_domain_endpoint": props['opensearch_domain_endpoint'],
            "web_root_url": props['web_root_url'],
            "image_root_url": props['image_root_url'],
            "pinpoint_app_id": props['pinpoint_app_id'],
            "cluster": props['cluster'],
            "desired_count": "1",
            "log_group": props['log_group'],
            "source_security_group": self.load_balancer.security_group,
            "subnet1": props['subnet1'],
            "subnet2": props['subnet2'],
            "target_group": self.load_balancer.target_group,
            "service_discovery_namespace": props['service_discovery_namespace'],
            "stack_name": props['stack_name']
        }
        service = ServiceStack(self, "Service",
                               props=service_props)

        pipeline_props = {
            "service_name": props['service_name'],
            "fargate_service_name": service.fargate_service.attr_name,
            "logging_bucket": props['logging_bucket'],
            "service_path": props['service_path'],
            "user_pool_id": props['user_pool_id'],
            "user_pool_client_id": props['user_pool_client_id'],
            "identity_pool_id": props['identity_pool_id'],
            "products_service_external_url": "",
            "users_service_external_url": "",
            "carts_service_external_url": "",
            "videos_service_external_url": "",
            "orders_service_external_url": "",
            "recommendations_service_external_url": "",
            "search_service_external_url": "",
            "pinpoint_app_id": props['pinpoint_app_id'],
            "parameter_personalize_event_tracker_id": props['parameter_personalize_event_tracker_id'],
            "parameter_amplitude_api_key": props['parameter_amplitude_api_key'],
            "parameter_optimizely_sdk_key": props['parameter_optimizely_sdk_key'],
            "web_root_url": props['web_root_url'],
            "image_root_url": props['image_root_url'],
            "delete_repository_lambda_arn": props['delete_repository_lambda'].function_arn,
            "github_user": props['github_user'],
            "github_repo": props['github_repo'],
            "github_branch": props['github_branch'],
            "github_token": props['github_token'],
            "cluster_name": props['cluster'].cluster_name,
            "task_execution_role": service.task_execution_role,
            "task_role": service.task_role,
            "source_deployment_type": props['source_deployment_type'],
            "cleanup_bucket_lambda_arn": props['cleanup_bucket_lambda_arn'],
            "stack_name": props['stack_name']
        }
        PipelineStack(self, "Pipeline",
                      props=pipeline_props)
