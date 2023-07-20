from aws_cdk import (
    Stack,
    Aws,
    aws_s3 as s3,
    aws_iam as iam,
    CustomResource,
    RemovalPolicy
)
from constructs import Construct

class BucketStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        self.logging_bucket = s3.Bucket(self, "LoggingBucket",
                                        removal_policy=RemovalPolicy.DESTROY,
                                        versioned=True,
                                        encryption=s3.BucketEncryption.S3_MANAGED)

        self.logging_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                principals=[iam.ServicePrincipal("logging.s3.amazonaws.com")],
                resources=[
                    self.logging_bucket.bucket_arn,
                    f"{self.logging_bucket.bucket_arn}/*"
                ],
                conditions={
                    "StringEquals": {"aws:SourceAccount": [Aws.ACCOUNT_ID]}
                }
            )
        )

        self.stack_bucket = s3.Bucket(self, "StackBucket",
                                      removal_policy=RemovalPolicy.DESTROY,
                                      versioned=True,
                                      encryption=s3.BucketEncryption.S3_MANAGED,
                                      server_access_logs_bucket=self.logging_bucket,
                                      server_access_logs_prefix="stack-logs")

        """
        Empties buckets when stack is deleted
        """

        CustomResource(self, "EmptyStackBucket",
                       resource_type="Custom::EmptyStackBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties={
                           "BucketName": self.stack_bucket.bucket_name
                       })

        CustomResource(self, "EmptyLoggingBucket",
                       resource_type="Custom::EmptyStackBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties={
                           "BucketName":self.logging_bucket.bucket_name
                       })