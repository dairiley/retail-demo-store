from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam
)
from constructs import Construct

class OpenSearchSLRStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        iam.CfnServiceLinkedRole(self, "OpenSearchServiceLinkedRole",
                                 aws_service_name="opensearchservice.amazonaws.com",
                                 description="Role for OpenSearch to access resources in VPC")
