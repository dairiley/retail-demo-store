from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam
)
from constructs import Construct

class PersonalizeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        props['stack_bucket'].add_to_resource_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                resources=[
                    props['stack_bucket'].bucket_arn,
                    f"{props['stack_bucket'].bucket_arn}/*"
                ],
                principals=[iam.ServicePrincipal("personalize.amazonaws.com")]
            )
        )

        self.personalize_role = iam.Role(self, "PersonalizeServiceRole",
                                         role_name=f"{props['uid']}-PersonalizeS3",
                                         assumed_by=iam.ServicePrincipal("personalize.amazonaws.com"),
                                         inline_policies={
                                             "BucketAccess": iam.PolicyDocument(
                                                 statements=[iam.PolicyStatement(
                                                 actions=[
                                                     "s3:GetObject",
                                                     "s3:ListBucket",
                                                     "s3:PutObject"
                                                 ],
                                                 resources=[
                                                     f"arn:aws:s3:::{props['resource_bucket']}",
                                                     f"arn:aws:s3:::{props['resource_bucket']}/*",
                                                     props['stack_bucket'].bucket_arn,
                                                     f"{props['stack_bucket'].bucket_arn}/*"
                                                 ])]
                                             )
                                         })
