from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_secretsmanager as secretsmanager,
    SecretValue,
    aws_s3 as s3
)
from constructs import Construct

class AmazonPayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        amazon_pay_private_key_secret = secretsmanager.Secret(self, "AmazonPayPrivateKeySecret",
                                                              secret_name="AmazonPayPrivateKey",
                                                              secret_string_value=SecretValue.unsafe_plain_text(props['amazon_pay_private_key']))

        amazon_pay_signing_lambda_role = iam.Role(self, "AmazonPaySigningLambdaExecutionRole",
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
                                                actions=["secretsmanager:GetSecretValue"],
                                                resources=[amazon_pay_private_key_secret.secret_arn]
                                            )]
                                        )
                                    })

        self.amazon_pay_signing_lambda = lambda_.Function(self, "AmazonPaySigningLambda",
                                                          runtime=lambda_.Runtime.NODEJS_12_X,
                                                          description="Signs Amazon Pay payloads to be used with Amazon Pay button",
                                                          handler="amazon-pay-signing.handler",
                                                          function_name="AmazonPaySigningLambda",
                                                          code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "AmazonPaySigningLambdaBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/amazon-pay-signing.zip"),
                                                          timeout=Duration.seconds(30),
                                                          role=amazon_pay_signing_lambda_role,
                                                          environment={
                                                              "AmazonPayPublicKeyId": props['amazon_pay_public_key_id'],
                                                              "AmazonPayPrivateKeySecretArn": amazon_pay_private_key_secret.secret_arn,
                                                              "WebURL": props['web_url']
                                                          })
