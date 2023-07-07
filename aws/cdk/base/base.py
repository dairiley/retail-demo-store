from aws_cdk import Aws, Stack, aws_iam as iam
from .authentication import AuthenticationStack
from .buckets import BucketStack
from .cloudfront import CloudFrontStack
from .codecommit import CodeCommitStack
from .ecs_cluster import ECSClusterStack
from .evidently import EvidentlyStack
from .notebook import NotebookStack
from .opensearch import OpenSearchStack
from .personalize import PersonalizeStack
from .pinpoint import PinpointStack
from .servicediscovery import ServiceDiscoveryStack
from .ssm import SsmStack
from .tables import TablesStack
from .vpc import VpcStack
from .opensearch_slr import OpenSearchSLRStack
from .acm_cert import AcmCertStack
from constructs import Construct

class BaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        uid = f"{props['stack_name']}-{Aws.REGION}"

        self.pinpoint = PinpointStack(self, "Pinpoint")

        auth_props = {
            "auth_name": uid,
            "pinpoint_app_id": self.pinpoint.pinpoint.ref
        }
        self.authentication = AuthenticationStack(self, "Authentication",
                                                  props=auth_props)

        vpc_props = {
            "stack_name": props['stack_name']
        }
        self.vpc = VpcStack(self, "Vpc",
                            vpc_props)

        bucket_props = {
            "cleanup_bucket_lambda_arn": props['cleanup_bucket_lambda_arn']
        }
        self.buckets = BucketStack(self, "Buckets",
                                   bucket_props)

        self.tables = TablesStack(self, "Tables")

        service_discovery_props = {
            "vpc": self.vpc.vpc
        }
        self.service_discovery = ServiceDiscoveryStack(self, "ServiceDiscovery",
                                                       service_discovery_props)

        ecs_cluster_props = {
            "stack_name": props['stack_name']
        }
        self.ecs_cluster = ECSClusterStack(self, "ECSCluster",
                                           props=ecs_cluster_props)

        if props['create_opensearch_service_role']:
            opensearch_slr = OpenSearchSLRStack(self, "OpenSearchServiceLinkedRole")
            self.vpc.add_dependency(opensearch_slr)

        opensearch_props = {
            "vpc": self.vpc.vpc,
            "subnet1": self.vpc.subnet1
        }
        self.opensearch = OpenSearchStack(self, "OpenSearch",
                                          props=opensearch_props)

        ssm_props = {
            "stack_bucket_name": self.buckets.stack_bucket.bucket_name,
            "experiment_strategy_table_name": self.tables.experiment_strategy_table.ref,
            "amplitude_api_key": props['amplitude_api_key'],
            "optimizely_sdk_key": props['optimizely_sdk_key'],
            "segment_write_key": props['segment_write_key'],
            "mparticle_org_id": props['mparticle_org_id'],
            "mparticle_api_key": props['mparticle_api_key'],
            "mparticle_secret_key": props['mparticle_secret_key'],
            "mparticle_s2s_api_key": props['mparticle_s2s_api_key'],
            "mparticle_s2s_secret_key": props['mparticle_s2s_secret_key'],
            "pinpoint_sms_long_code": props['pinpoint_sms_long_code'],
            "google_analytics_measurement_id": props['google_analytics_measurement_id']
        }
        self.ssm = SsmStack(self, "SSMParameters",
                            props=ssm_props)

        codecommit_props = {
            "resource_bucket": props['resource_bucket'],
            "source_deployment_type": props['source_deployment_type']
        }
        CodeCommitStack(self, "CodeCommitRepository",
                        props=codecommit_props)

        cloudfront_props = {
            "cleanup_bucket_lambda_arn": props['cleanup_bucket_lambda_arn'],
            "logging_bucket": self.buckets.logging_bucket
        }
        self.distribution = CloudFrontStack(self, "CloudFront",
                                            props=cloudfront_props)

        personalize_props = {
            "uid": uid,
            "stack_bucket": self.buckets.stack_bucket,
            "resource_bucket": props['resource_bucket']
        }
        self.personalize = PersonalizeStack(self, "Personalize",
                                            props=personalize_props)

        self.evidently_project_name = uid
        evidently_props = {
            "uid": self.evidently_project_name
        }
        EvidentlyStack(self, "Evidently",
                       props=evidently_props)

        self.acm_cert = AcmCertStack(self, "SelfSignedCertACM")

        notebook_props = {
            "github_user": props['github_user'],
            "github_branch": props['github_branch'],
            "uid": uid,
            "parent_stack_name": props['stack_name'],
            "stack_bucket_arn": self.buckets.stack_bucket.bucket_arn,
            "resource_bucket": props['resource_bucket'],
            "experiment_strategy_table_arn": self.tables.experiment_strategy_table.attr_arn,
            "evidently_project_name": self.evidently_project_name,
            "user_pool_arn": self.authentication.user_pool.attr_arn,
            "user_pool_id": self.authentication.user_pool.ref,
            "vpc": self.vpc.vpc,
            "subnet1": self.vpc.subnet1,
            "pinpoint_app_id": self.pinpoint.pinpoint.ref
        }
        self.notebook = NotebookStack(self, "Notebook",
                                      props=notebook_props)

        