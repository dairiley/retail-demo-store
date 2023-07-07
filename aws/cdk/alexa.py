from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_s3 as s3,
)
from constructs import Construct

class AlexaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        alexa_skill_role = iam.Role(self, "AlexaSkillIAMRole",
                            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                            inline_policies={
                                "AlexaLambdaExecutionPolicy": iam.PolicyDocument(
                                    statements=[
                                         iam.PolicyStatement(
                                             actions=["mobiletargeting:SendMessages"],
                                             resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/messages"]
                                         ),
                                         iam.PolicyStatement(
                                             actions=["mobiletargeting:GetEmailChannel"],
                                             resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/channels/email"]
                                         ),
                                         iam.PolicyStatement(
                                             actions=[
                                                 "geo:SearchPlaceIndexForPosition",
                                                 "geo:SearchPlaceIndexForText"
                                             ],
                                             resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:place-index/{props['location_resource_name']}*"]
                                         ),
                                         iam.PolicyStatement(
                                             actions=[
                                                 "logs:CreateLogStream",
                                                 "logs:PutLogEvents",
                                                 "logs:CreateLogGroup"
                                             ],
                                             resources=["*"]
                                         )
                                    ]
                                )
                            })

        self.alexa_skill_function = lambda_.Function(self, "AlexaSkillFunction",
                                                     runtime=lambda_.Runtime.PYTHON_3_8,
                                                     handler="alexa-skill-lambda.lambda_handler",
                                                     code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "AlexaSkillFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/alexa-skill-lambda.zip"),
                                                     timeout=Duration.seconds(60),
                                                     role=alexa_skill_role,
                                                     memory_size=512,
                                                     environment={
                                                         "OrdersServiceExternalUrl": props['orders_service_external_url'],
                                                         "CartsServiceExternalUrl": props['carts_service_external_url'],
                                                         "RecommendationsServiceExternalUrl": props['recommendations_service_external_url'],
                                                         "ProductsServiceExternalUrl": props['products_service_external_url'],
                                                         "LocationServiceExternalUrl": props['location_service_external_url'],
                                                         "PinpointAppId": props['pinpoint_app_id'],
                                                         "LocationResourceName": props['location_resource_name'],
                                                         "AlexaDefaultSandboxEmail": props['alexa_default_sandbox_email']
                                                     })

        self.alexa_skill_function.add_permission("AlexaSkillFunctionEventPermission",
                                            principal=iam.ServicePrincipal("alexa-appkit.amazon.com"),
                                            event_source_token=props['alexa_skill_id'])

        self.alexa_skill_function.add_permission("AlexaSkillFunctionEventPermissionSmartHome",
                                            principal=iam.ServicePrincipal("alexa-connectedhome.amazon.com"),
                                            event_source_token=props['alexa_skill_id'])

        logs.LogGroup(self, "ACMImportCertLambdaFunLogGroup",
                      log_group_name=f"/aws/lambda/{self.alexa_skill_function.function_name}",
                      retention=logs.RetentionDays.TWO_WEEKS)
