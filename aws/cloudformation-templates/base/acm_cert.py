from aws_cdk import (
    Stack,
    Aws,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    Duration
)
from constructs import Construct

class AcmCertStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.acm_parameter_name = "/retaildemostore/acm-arn"
        acm_parameter = ssm.StringParameter(self, "ACMARNParameter",
                                            parameter_name=self.acm_parameter_name,
                                            string_value="Dummy",
                                            description="Retail Demo Store ACM Arn")

        acm_import_fn_execution_role = iam.Role(self, "ACMimportCertLambdaExecutionRole",
                                                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                inline_policies={
                                                    "CustomPolicy": iam.PolicyDocument(
                                                         statements=[iam.PolicyStatement(
                                                             actions=[
                                                                 "logs:CreateLogStream",
                                                                 "logs:DescribeLogStreams",
                                                                 "logs:PutLogEvents",
                                                                 "ssm:GetParameter",
                                                                 "ssm:PutParameter",
                                                                 "acm:ImportCertificate",
                                                                 "acm:DeleteCertificate",
                                                                 "acm:AddTagsToCertificate",
                                                                 "s3:GetObject"
                                                             ],
                                                             resources=[
                                                                 f"arn:aws:logs:${Aws.REGION}:${Aws.ACCOUNT_ID}:log-group:*",
                                                                 f"arn:aws:ssm:${Aws.REGION}:${Aws.ACCOUNT_ID}:parameter/retaildemostore/acm-arn",
                                                                 f"arn:aws:acm:${Aws.REGION}:${Aws.ACCOUNT_ID}:certificate/*",
                                                                 "arn:aws:s3:::retail-demo-store-code/keys/*"
                                                             ]
                                                         )]
                                                    )
                                                })

        acm_import_fn = lambda_.Function(self, "ACMimportCertLambdaFunction",
                                         runtime=lambda_.Runtime.PYTHON_3_9,
                                         description="Retail Demo Store acm-import-certificate function that returns ARN for imported certificate",
                                         handler="index.handler",
                                         code=lambda_.Code.from_asset("base/lambda/acm_import_cert"),
                                         timeout=Duration.seconds(120),
                                         role=acm_import_fn_execution_role)
        acm_import_fn.node.add_dependency(acm_parameter)


        logs.LogGroup(self, "ACMImportCertLambdaFunLogGroup",
                      log_group_name=f"/aws/lambda/{acm_import_fn.function_name}",
                      retention=logs.RetentionDays.THREE_DAYS)






