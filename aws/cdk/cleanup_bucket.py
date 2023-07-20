from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    BundlingOptions
)
from constructs import Construct

class CleanupBucketStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cleanup_bucket_lambda_role = iam.Role(self, "CleanupBucketLambdaExecutionRole",
                                              assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                              inline_policies={
                                                  "LoggingPolicy": iam.PolicyDocument(statements=[
                                                      iam.PolicyStatement(
                                                          actions=[
                                                              "logs:CreateLogStream",
                                                              "logs:PutLogEvents",
                                                              "logs:CreateLogGroup"
                                                          ],
                                                          resources=["*"]
                                                       )]
                                                  ),
                                                  "S3Policy": iam.PolicyDocument(statements=[
                                                      iam.PolicyStatement(
                                                          actions=[
                                                              "s3:List*",
                                                              "s3:DeleteObject",
                                                              "s3:DeleteObjectVersion"
                                                          ],
                                                          resources=["*"]
                                                      )
                                                  ])
                                              })

        self.function = lambda_.Function(self, "CleanupBucketLambdaFunction",
                                         runtime=lambda_.Runtime.PYTHON_3_7,
                                         description="Retail Demo Store deployment utility function that deletes all objects in an S3 bucket when the CloudFormation stack is deleted",
                                         handler="index.handler",
                                         code=lambda_.Code.from_asset("lambda/cleanup_bucket",
                                                                      bundling=BundlingOptions(
                                                                          image=lambda_.Runtime.PYTHON_3_7.bundling_image,
                                                                          command=[
                                                                              "bash", "-c",
                                                                              "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                                                                          ],
                                                                      )),
                                         timeout=Duration.seconds(300),
                                         role=cleanup_bucket_lambda_role)

