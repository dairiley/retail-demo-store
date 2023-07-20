from aws_cdk import aws_ssm as ssm
from base.base import BaseStack
from services.services import ServicesStack
from web_ui_pipeline import WebUIPipelineStack
from swagger_ui_pipeline import SwaggerUIPipelineStack
from lex import LexStack
from amazonpay import AmazonPayStack
from location import LocationStack
from alexa import AlexaStack
from deployment_support import DeploymentSupportStack
from segment import SegmentStack
from mparticle import MParticleStack
from constructs import Construct
from cleanup_bucket import CleanupBucketStack
from aws_cdk import CfnOutput, Stack, Aws

class RetailDemoStoreStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        Stack Parameters
        Set custom values before deployment in cdk.json
        """

        stack_name = self.node.try_get_context("stack_name")

        deployment_config = self.node.try_get_context("retail_demo_store_deployment_configuration")
        resource_bucket = deployment_config["resource_bucket"]
        resource_bucket_relative_path = deployment_config["resource_bucket_relative_path"]
        create_opensearch_service_role = deployment_config["create_opensearch_service_role"]

        source_deployment_approach = self.node.try_get_context("source_deployment_approach")
        source_deployment_type = source_deployment_approach["source_deployment_type"]
        github_repository = source_deployment_approach["github_repository"]
        github_branch = github_repository["github_branch"]
        github_user = github_repository["github_user"] if source_deployment_type == "GitHub Repository" else False
        github_repo = github_repository["github_repo"]
        github_token = github_repository["github_token"]

        auto_build_resources = self.node.try_get_context("auto_build_resources")
        pre_index_opensearch = auto_build_resources["pre_index_opensearch"]
        pre_create_personalize_resources = auto_build_resources["pre_create_personalize_resources"]
        pre_create_pinpoint_workshop = auto_build_resources["pre_create_pinpoint_workshop"]
        pinpoint_email_from_address = auto_build_resources["pinpoint_email_from_address"]
        pinpoint_email_from_name = auto_build_resources["pinpoint_email_from_name"]
        pinpoint_sms_long_code = auto_build_resources["pinpoint_sms_long_code"]

        use_default_ivs_streams = self.node.try_get_context("use_default_ivs_streams")

        create_location_and_personalized_offers_resources = self.node.try_get_context("create_location_and_personalized_offers_resources")
        deploy_location_services = create_location_and_personalized_offers_resources["deploy_location_services"]
        deploy_personalized_offers_campaign = create_location_and_personalized_offers_resources["deploy_personalized_offers_campaign"]

        amazon_pay = self.node.try_get_context("amazon_pay")
        amazon_pay_merchant_id = amazon_pay["amazon_pay_merchant_id"]
        amazon_pay_store_id = amazon_pay["amazon_pay_store_id"]
        amazon_pay_public_key_id = amazon_pay["amazon_pay_public_key_id"]
        amazon_pay_private_key = amazon_pay["amazon_pay_private_key"]

        alexa_convenience_store_demo = self.node.try_get_context("alexa_convenience_store_demo")
        alexa_skill_id = alexa_convenience_store_demo["alexa_skill_id"]
        alexa_default_sandbox_email = alexa_convenience_store_demo["alexa_default_sandbox_email"]

        optional_integrations = self.node.try_get_context("optional_integrations")
        amplitude_api_key = optional_integrations["amplitude_api_key"]
        optimizely_sdk_key = optional_integrations["optimizely_sdk_key"]
        deploy_segment_resources = optional_integrations["include_segment_dependencies"]
        segment_write_key = optional_integrations["segment_write_key"]
        deploy_mparticle_resources = optional_integrations["mparticle_dependencies"]
        mparticle_org_id = optional_integrations["mparticle_org_id"]
        mparticle_api_key = optional_integrations["mparticle_api_key"]
        mparticle_secret_key = optional_integrations["mparticle_secret_key"]
        mparticle_s2s_api_key = optional_integrations["mparticle_s2s_api_key"]
        mparticle_s2s_secret_key = optional_integrations["mparticle_s2s_secret_key"]
        google_analytics_measurement_id = optional_integrations["google_analytics_measurement_id"]

        fenix_commerce_edd_integration = self.node.try_get_context("fenix_commerce_edd_integration")
        fenix_zip_detect_url = fenix_commerce_edd_integration["fenix_zip_detect_url"]
        fenix_tenant_id = fenix_commerce_edd_integration["fenix_tenant_id"]
        fenix_edd_endpoint = fenix_commerce_edd_integration["fenix_edd_endpoint"]
        fenix_monetary_value = fenix_commerce_edd_integration["fenix_monetary_value"]
        fenix_enabled_pdp = fenix_commerce_edd_integration["fenix_enabled_pdp"]
        fenix_enabled_cart = fenix_commerce_edd_integration["fenix_enabled_cart"]
        fenix_enabled_checkout = fenix_commerce_edd_integration["fenix_enabled_checkout"]
        fenix_xapi_key = fenix_commerce_edd_integration["fenix_xapi_key"]

        cleanup_bucket = CleanupBucketStack(self, "CleanupBucket")

        base_props = {
            "resource_bucket": resource_bucket,
            "resource_bucket_relative_path": resource_bucket_relative_path,
            "source_deployment_type": source_deployment_type,
            "create_opensearch_service_role": create_opensearch_service_role,
            "cleanup_bucket_lambda_arn": cleanup_bucket.function.function_arn,
            "amplitude_api_key": amplitude_api_key,
            "stack_name": stack_name,
            "optimizely_sdk_key": optimizely_sdk_key,
            "segment_write_key": segment_write_key,
            "mparticle_org_id": mparticle_org_id,
            "mparticle_api_key": mparticle_api_key,
            "mparticle_secret_key": mparticle_secret_key,
            "mparticle_s2s_api_key": mparticle_s2s_api_key,
            "mparticle_s2s_secret_key": mparticle_s2s_secret_key,
            "google_analytics_measurement_id": google_analytics_measurement_id,
            "pinpoint_sms_long_code": pinpoint_sms_long_code,
            "github_user": github_user,
            "github_branch": github_branch,
            "location_resource_prefix": stack_name,
            "fenix_zip_detect_url": fenix_zip_detect_url,
            "fenix_tenant_id": fenix_tenant_id,
            "fenix_edd_endpoint": fenix_edd_endpoint,
            "fenix_monetary_value": fenix_monetary_value,
            "fenix_enabled_pdp": fenix_enabled_pdp,
            "fenix_enabled_cart": fenix_enabled_cart,
            "fenix_enabled_checkout": fenix_enabled_checkout,
            "fenix_xapi_key": fenix_xapi_key}
        base = BaseStack(self, "Base",
                         props=base_props)

        amazonpay = False
        if "" not in [amazon_pay_merchant_id, amazon_pay_store_id, amazon_pay_public_key_id, amazon_pay_private_key]:
            amazonpay_props = {
                "resource_bucket": resource_bucket,
                "resource_bucket_relative_path": resource_bucket_relative_path,
                "amazon_pay_public_key_id": amazon_pay_public_key_id,
                "amazon_pay_store_id": amazon_pay_store_id,
                "amazon_pay_private_key": amazon_pay_private_key,
                "web_url": f"http://{base.distribution.distribution.distribution_domain_name}"
            }
            amazonpay = AmazonPayStack(self, "AmazonPay",
                                       props=amazonpay_props)

        services_props = {
            "resource_bucket": resource_bucket,
            "resource_bucket_relative_path": resource_bucket_relative_path,
            "source_deployment_type": source_deployment_type,
            "github_repo": github_repo,
            "github_branch": github_branch,
            "github_user": github_user,
            "github_token": github_token,
            "user_pool_id": base.authentication.user_pool.ref,
            "user_pool_client_id": base.authentication.user_pool_id_str,
            "identity_pool_id": base.authentication.identity_pool.ref,
            "subnet1": base.vpc.subnet1,
            "subnet2": base.vpc.subnet2,
            "vpc": base.vpc.vpc,
            "cluster": base.ecs_cluster.cluster,
            "amazon_pay_signing_lambda": amazonpay.amazon_pay_signing_lambda if amazonpay else False,
            "service_discovery_namespace": base.service_discovery.name,
            "products_table": base.tables.products_table,
            "categories_table": base.tables.categories_table,
            "experiment_strategy_table": base.tables.experiment_strategy_table,
            "pinpoint_app_id": base.pinpoint.pinpoint.ref,
            "parameter_personalize_event_tracker_id": base.ssm.parameter_personalize_event_tracker_id.string_value,
            "parameter_amplitude_api_key": amplitude_api_key,
            "parameter_optimizely_sdk_key": optimizely_sdk_key,
            "parameter_ivs_video_channel_map": base.ssm.parameter_ivs_video_channel_map.string_value,
            "cleanup_bucket_lambda_arn": cleanup_bucket.function.function_arn,
            "web_root_url": base.distribution.distribution.distribution_domain_name,
            "image_root_url": f"{base.distribution.distribution.distribution_domain_name}/images/",
            "stack_name": stack_name,
            "evidently_project_name": base.evidently_project_name,
            "opensearch_domain_endpoint": base.opensearch.domain.attr_domain_endpoint,
            "acm_cert_arn": ssm.StringParameter.from_string_parameter_attributes(self, "ACMCertValue", parameter_name=base.acm_cert.acm_parameter_name).string_value,
            "logging_bucket": base.buckets.logging_bucket
        }
        services = ServicesStack(self, "Services",
                                 props=services_props)

        """
        Amazon Location Resources
        """
        location_props = {
            "resource_bucket": resource_bucket,
            "resource_bucket_relative_path": resource_bucket_relative_path,
            "user_pool_id": base.authentication.user_pool.ref,
            "deploy_default_geofence": deploy_personalized_offers_campaign,
            "pinpoint_app_id": base.pinpoint.pinpoint.ref,
            "pinpoint_email_from_address": pinpoint_email_from_address,
            "products_service_external_url": services.products.load_balancer.service_url,
            "users_service_external_url": services.users.load_balancer.service_url,
            "carts_service_external_url": services.carts.load_balancer.service_url,
            "orders_service_external_url": services.orders.load_balancer.service_url,
            "offers_service_external_url": services.offers.load_balancer.service_url,
            "web_url": f"http://{base.distribution.distribution.distribution_domain_name}"
        }
        location_notification_endpoint = False
        if deploy_location_services:
            location = LocationStack(self, "Location",
                                     props=location_props)
            location_notification_endpoint = location.location_notification_endpoint

        location_resource_name = deploy_location_services if deploy_location_services else "NotDeployed"


        webui_props = {
            "resource_bucket": resource_bucket,
            "resource_bucket_relative_path": resource_bucket_relative_path,
            "stack_name": stack_name,
            "web_root_url": base.distribution.distribution.distribution_domain_name,
            "image_root_url": f"{base.distribution.distribution.distribution_domain_name}/images/",
            "source_deployment_type": source_deployment_type,
            "github_repo": github_repo,
            "github_branch": github_branch,
            "github_token": github_token,
            "github_user": github_user,
            "amazon_pay_merchant_id": amazon_pay_merchant_id,
            "amazon_pay_public_key_id": amazon_pay_public_key_id,
            "amazon_pay_store_id": amazon_pay_store_id,
            "web_ui_bucket": base.distribution.webui_bucket,
            "web_ui_cdn": base.distribution.distribution.distribution_id,
            "user_pool_id": base.authentication.user_pool.ref,
            "user_pool_client_id": base.authentication.user_pool_id_str,
            "identity_pool_id": base.authentication.identity_pool.ref,
            "products_service_external_url": services.products.load_balancer.service_url,
            "users_service_external_url": services.users.load_balancer.service_url,
            "carts_service_external_url": services.carts.load_balancer.service_url,
            "orders_service_external_url": services.orders.load_balancer.service_url,
            "recommendations_service_external_url": services.recommendations.load_balancer.service_url,
            "search_service_external_url": services.search.load_balancer.service_url,
            "offers_service_external_url": services.offers.load_balancer.service_url,
            "videos_service_external_url": services.videos.load_balancer.service_url,
            "location_service_external_url": services.location.load_balancer.service_url,
            "location_notification_endpoint": location_notification_endpoint if location_notification_endpoint else "",
            "pinpoint_app_id": base.pinpoint.pinpoint.ref,
            "parameter_personalize_event_tracker_id": base.ssm.parameter_personalize_event_tracker_id.string_value,
            "parameter_amplitude_api_key": amplitude_api_key,
            "parameter_optimizely_sdk_key": optimizely_sdk_key,
            "parameter_segment_write_key": segment_write_key,
            "fenix_zip_detect_url": fenix_zip_detect_url,
            "fenix_tenant_id": fenix_tenant_id,
            "fenix_edd_endpoint": fenix_edd_endpoint,
            "fenix_monetary_value": fenix_monetary_value,
            "fenix_enabled_pdp": fenix_enabled_pdp,
            "fenix_enabled_cart": fenix_enabled_cart,
            "fenix_enabled_checkout": fenix_enabled_checkout,
            "fenix_xapi_key": fenix_xapi_key,
            "logging_bucket": base.buckets.logging_bucket,
            "google_analytics_measurement_id": google_analytics_measurement_id,
            "cleanup_bucket_lambda_arn": cleanup_bucket.function.function_arn,
            "location_resource_name": location_resource_name
        }
        WebUIPipelineStack(self, "WebUIPipeline",
                           props=webui_props)

        swaggerui_props = {
            "resource_bucket": resource_bucket,
            "resource_bucket_relative_path": resource_bucket_relative_path,
            "stack_name": stack_name,
            "source_deployment_type": source_deployment_type,
            "github_repo": github_repo,
            "github_branch": github_branch,
            "github_token": github_token,
            "github_user": github_user,
            "swagger_ui_cdn": base.distribution.swaggerui_distribution,
            "swagger_ui_bucket_arn": base.distribution.swaggerui_bucket.bucket_arn,
            "swagger_ui_bucket_name": base.distribution.swaggerui_bucket.bucket_name,
            "swagger_ui_root_url": base.distribution.swaggerui_distribution.distribution_domain_name,
            "products_service_external_url": services.products.load_balancer.service_url,
            "users_service_external_url": services.users.load_balancer.service_url,
            "carts_service_external_url": services.carts.load_balancer.service_url,
            "orders_service_external_url": services.orders.load_balancer.service_url,
            "recommendations_service_external_url": services.recommendations.load_balancer.service_url,
            "search_service_external_url": services.search.load_balancer.service_url,
            "videos_service_external_url": services.videos.load_balancer.service_url,
            "location_service_external_url": services.location.load_balancer.service_url,
            "offers_service_external_url": services.offers.load_balancer.service_url,
            "logging_bucket": base.buckets.logging_bucket,
            "cleanup_bucket_lambda_arn": cleanup_bucket.function.function_arn
        }
        SwaggerUIPipelineStack(self, "SwaggerUIPipeline",
                               props=swaggerui_props)

        """
        Lex personalization function
        """
        lex_props = {
        "resource_bucket": resource_bucket,
        "resource_bucket_relative_path": resource_bucket_relative_path,
        "users_service_external_url": services.users.load_balancer.service_url,
        "recommendations_service_external_url": services.recommendations.load_balancer.service_url
        }
        LexStack(self, "ChatbotFunctions",
                 props=lex_props)

        if alexa_skill_id != "":
            alexa_props = {
                "alexa_skill_id": alexa_skill_id,
                "pinpoint_app_id": base.pinpoint.pinpoint.ref,
                "resource_bucket": resource_bucket,
                "resource_bucket_relative_path": resource_bucket_relative_path,
                "products_service_external_url": services.products.load_balancer.service_url,
                "location_service_external_url": services.location.load_balancer.service_url,
                "carts_service_external_url": services.carts.load_balancer.service_url,
                "orders_service_external_url": services.orders.load_balancer.service_url,
                "recommendations_service_external_url": services.recommendations.load_balancer.service_url,
                "location_resource_name": location_resource_name,
                "alexa_default_sandbox_email": alexa_default_sandbox_email
            }
            alexa = AlexaStack(self, "Alexa",
                               props=alexa_props)

            deployment_support_props = {
                "resource_bucket": resource_bucket,
                "resource_bucket_relative_path": resource_bucket_relative_path,
                "pre_index_opensearch": pre_index_opensearch,
                "pre_create_personalize_resources": pre_create_personalize_resources,
                "subnet1": base.vpc.subnet1,
                "subnet2": base.vpc.subnet2,
                "opensearch_security_group": base.opensearch.security_group,
                "opensearch_domain_arn": base.opensearch.domain.attr_arn,
                "opensearch_domain_endpoint": base.opensearch.domain.attr_domain_endpoint,
                "parameter_ivs_video_channel_map": base.ssm.parameter_ivs_video_channel_map.string_value,
                "pre_create_pinpoint_workshop": pre_create_pinpoint_workshop,
                "uid": f"{stack_name}-{Aws.REGION}",
                "vpc":  base.vpc.vpc,
                "pinpoint_app_id": base.pinpoint.pinpoint.ref,
                "pinppint_personalize_role_arn": services.pinpoint_personalize.pinpoint_personalize_role.role_arn,
                "customize_recommendations_function_arn": services.pinpoint_personalize.customize_recommendations_function.function_arn,
                "customize_offers_recommendations_function_arn": services.pinpoint_personalize.customize_offers_recommendations_function.function_arn,
                "pinpoint_email_from_address": pinpoint_email_from_address,
                "pinpoint_email_from_name": pinpoint_email_from_name,
                "use_default_ivs_streams": use_default_ivs_streams,
                "products_service_external_url": services.products.load_balancer.service_url,
                "deploy_personalized_offers_campaign": deploy_personalized_offers_campaign,
                "personalize_role_arn": base.personalize.personalize_role.role_arn
            }
            deployment_support = DeploymentSupportStack(self, "DeploymentSupport",
                                                        props=deployment_support_props)
            # Delay towards end of deployment so that ES domain and DNS changes become consistent
            deployment_support.add_dependency(services)
            deployment_support.add_dependency(base)

            """
            Segment Lambda Functions and Roles
            """
            if deploy_segment_resources:
                segment_props = {
                    "resource_bucket": resource_bucket,
                    "resource_bucket_relative_path": resource_bucket_relative_path
                }
                SegmentStack(self, "SegmentPersonalize",
                             props=segment_props)

            """
            mParticle Lambda Functions Kinesis and Roles
            """
            if deploy_mparticle_resources:
                mparticle_props = {
                    "resource_bucket": resource_bucket,
                    "resource_bucket_relative_path": resource_bucket_relative_path,
                    "mparticle_org_id": mparticle_org_id,
                    "uid": f"{stack_name}-{Aws.REGION}"
                }
                MParticleStack(self, "mParticlePersonalize",
                               props=mparticle_props)

            """
            Stack Outputs
            """

            CfnOuput(self, "UserPoolId",
                     description="Authentication Cognito User Pool Id.",
                     value=base.authentication.user_pool.ref)

            CfnOuput(self, "UserPoolClientId",
                     description="Authentication Cognito User Pool Client Id.",
                     value=base.authentication.user_pool_id_str)

            CfnOuput(self, "IdentityPoolId",
                     description="Authentication Cognito Identity Pool Id.",
                     value=base.authentication.identity_pool.ref)

            CfnOuput(self, "BucketStackBucketName",
                     description="Stack Bucket Name.",
                     value=base.buckets.stack_bucket.bucket_name)

            CfnOuput(self, "NotebookInstanceId",
                     description="Notebook Instance Id.",
                     value=base.notebook.notebook.ref)

            CfnOuput(self, "VpcId",
                     description="VPC Id.",
                     value=base.vpc.vpc.vpc_id)

            CfnOuput(self, "Subnets",
                     description="Service Subnets.",
                     value=f"{base.vpc.subnet1.subnet_id}, {base.vpc.subnet2.subnet_id}")

            CfnOuput(self, "ClusterName",
                     description="ECS Cluster Name.",
                     value=base.ecs_cluster.cluster.cluster_name)

            CfnOuput(self, "WebURL",
                     description="Retail Demo Store Web UI URL.",
                     value=f"http://{base.distribution.distribution.distribution_domain_name}")

            CfnOuput(self, "OpenSearchDomainEndpoint",
                     description="OpenSearch Endpoint.",
                     value=base.opensearch.domain.attr_domain_endpoint)

            CfnOuput(self, "ParameterIVSVideoChannelMap",
                     description="Retail Demo Store video file to IVS channel mapping parameter.",
                     value=base.ssm.parameter_ivs_video_channel_map.string_value)

            CfnOuput(self, "PinpointAppId",
                     description="Pinpoint App Id.",
                     value=base.pinpoint.pinpoint.ref)

            CfnOuput(self, "AlexaSkillEndpointArn",
                     description="Arn of AWS Lambda function that can be a back-end.",
                     value=alexa.alexa_skill_function.function_arn)

            CfnOuput(self, "ProductsServiceUrl",
                     description="Products load balancer URL.",
                     value=services.products.load_balancer.service_url)

            CfnOuput(self, "UsersServiceUrl",
                     description="Users load balancer URL.",
                     value=services.users.load_balancer.service_url)

            CfnOuput(self, "CartsServiceUrl",
                     description="Carts load balancer URL.",
                     value=services.carts.load_balancer.service_url)

            CfnOuput(self, "OrdersServiceUrl",
                     description="Orders load balancer URL.",
                     value=services.orders.load_balancer.service_url)

            CfnOuput(self, "LocationServiceUrl",
                     description="Location load balancer URL.",
                     value=services.location.load_balancer.service_url)

            CfnOuput(self, "RecommendationsServiceUrl",
                     description="Recommendations load balancer URL.",
                     value=services.recommendations.load_balancer.service_url)

            CfnOuput(self, "VideosServiceUrl",
                     description="Videos load balancer URL.",
                     value=services.videos.load_balancer.service_url)

            CfnOuput(self, "OffersServiceUrl",
                     description="Offers service load balancer URL.",
                     value=services.offers.load_balancer.service_url)

            CfnOuput(self, "EvidentlyProjectName",
                     description="ARN for the CloudWatch Evidently project.",
                     value=base.evidently_project_name)

            CfnOuput(self, "ACMCertARN",
                     description="ARN for selfsigned cert for ELB.",
                     value=ssm.StringParameter.from_string_parameter_attributes(self, "ACMCertValue", parameter_name=base.acm_cert.acm_parameter_name).string_value)