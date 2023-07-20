from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_s3 as s3
)
from constructs import Construct

class LexStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bot_recommendations_lambda_role = iam.Role(self, "BotRecommendationsLambdaExecutionRole",
                                                   assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                   managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "BotRecommendationsLambdaExecutionRoleVPCAccess",
                                                                                                               managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")],
                                                   inline_policies={
                                                       "root": iam.PolicyDocument(
                                                           statements=[iam.PolicyStatement(
                                                               actions=[
                                                                   "logs:CreateLogStream",
                                                                   "logs:PutLogEvents",
                                                                   "logs:CreateLogGroup"
                                                               ],
                                                               resources=["*"]
                                                           )]
                                                       )
                                                   })

        bot_recommendations_lambda_function = lambda_.Function(self, "BotRecommendationsLambdaFunction",
                                                               runtime=lambda_.Runtime.PYTHON_3_8,
                                                               description="Retail Demo Store chatbot function that returns product recommendations as ResponseCards",
                                                               function_name="RetailDemoStore-Chat-Recommendations",
                                                               handler="bot-intent-recommendations.lambda_handler",
                                                               code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "BotRecommendationsLambdaFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/bot-intent-recommendations.zip"),
                                                               timeout=Duration.seconds(10),
                                                               role=bot_recommendations_lambda_role,
                                                               vpc=props['vpc'],
                                                               vpc_subnets=ec2.SubnetSelection(subnets=[props['private_subnet1'], props['private_subnet2']]),
                                                               environment={
                                                                   "users_service_base_url": props['users_service_external_url'],
                                                                   "recommendations_service_base_url": props['recommendations_service_external_url']
                                                               })

        bot_recommendations_lambda_function.add_permission("BotRecommendationsPermission",
                                                           principal=iam.ServicePrincipal("lex.amazonaws.com"),
                                                           source_arn=f"arn:aws:lex:{Aws.REGION}:{Aws.ACCOUNT_ID}:intent:RecommendProduct:*")
