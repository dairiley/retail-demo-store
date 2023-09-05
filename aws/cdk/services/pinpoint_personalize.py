from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_kms as kms,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_sns as sns
)
from constructs import Construct

class PinpointPersonalizeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.pinpoint_personalize_role = iam.Role(self, "PinpointPersonalizeRole",
                                                  assumed_by=iam.ServicePrincipal("pinpoint.amazonaws.com"),
                                                  role_name=f"{props['uid']}-PinptP9e",
                                                  managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "PinpointPersonalizeRoleVPCAccess",
                                                                                                              managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")],
                                                  inline_policies={
                                                      "PersonalizeAccess": iam.PolicyDocument(statements=[
                                                          iam.PolicyStatement(
                                                              actions=[
                                                                  "personalize:DescribeSolution",
                                                                  "personalize:DescribeCampaign",
                                                                  "personalize:GetRecommendations"
                                                              ],
                                                              resources=[
                                                                  f"arn:aws:personalize:{Aws.REGION}:{Aws.ACCOUNT_ID}:solution/retaildemo*",
                                                                  f"arn:aws:personalize:{Aws.REGION}:{Aws.ACCOUNT_ID}:campaign/retaildemo*",
                                                                  f"arn:aws:personalize:{Aws.REGION}:{Aws.ACCOUNT_ID}:filter/retaildemo*"
                                                              ]
                                                          )
                                                      ])
                                                  })

        customize_recommendations_lambda_role = iam.Role(self, "CustomizeRecommendationsFunctionRole",
                                                         assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                         managed_policies=[
                                                             iam.ManagedPolicy.from_managed_policy_arn(self,"CustomizeRecommendationsFunctionRoleVPCAccess",
                                                                                                       managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")],
                                                         inline_policies={
                                                             "CloudWatchAndPinpoint": iam.PolicyDocument(statements=[
                                                                 iam.PolicyStatement(
                                                                     actions=[
                                                                         "logs:CreateLogStream",
                                                                         "logs:PutLogEvents",
                                                                         "logs:CreateLogGroup"
                                                                     ],
                                                                     resources=["*"]
                                                                 ),
                                                                 iam.PolicyStatement(
                                                                     actions=["mobiletargeting:GetEndpoint"],
                                                                     resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/endpoints/*"]
                                                                 )
                                                             ])
                                                         })

        self.customize_recommendations_function = lambda_.Function(self, "CustomizeRecommendationsFunction",
                                                                   runtime=lambda_.Runtime.PYTHON_3_8,
                                                                   description="Retail Demo Store function called by Pinpoint to enrich messages with product information based on recommendations from Amazon Personalize",
                                                                   function_name="RetailDemoStorePinpointRecommender",
                                                                   handler="pinpoint-recommender.lambda_handler",
                                                                   code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "CustomizeRecommendationsFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/pinpoint-recommender.zip"),
                                                                   role=customize_recommendations_lambda_role,
                                                                   vpc=props['vpc'],
                                                                   allow_public_subnet=True,
                                                                   vpc_subnets=ec2.SubnetSelection(subnets=[props['private_subnet1'], props['private_subnet2']]),
                                                                   environment={"recommendations_service_host": props['recommendations_service_dns_name']})
        self.customize_recommendations_function.add_permission("PinpointPermission",
                                                           principal=iam.ServicePrincipal("pinpoint.amazonaws.com"),
                                                           source_arn=f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:*")

        self.customize_offers_recommendations_function = lambda_.Function(self, "CustomizeOffersRecommendationsFunction",
                                                                          runtime=lambda_.Runtime.PYTHON_3_8,
                                                                          description="Retail Demo Store function called by Pinpoint to enrich messages with product/offer information based on recommendations from Amazon Personalize",
                                                                          function_name="RetailDemoStorePinpointOffersRecommender",
                                                                          handler="pinpoint-offers-recommender.lambda_handler",
                                                                          code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "CustomizeOffersRecommendationsFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/pinpoint-offers-recommender.zip"),
                                                                          role=customize_recommendations_lambda_role,
                                                                          vpc=props['vpc'],
                                                                          allow_public_subnet=True,
                                                                          vpc_subnets=ec2.SubnetSelection(subnets=[props['private_subnet1'], props['private_subnet2']]),
                                                                          environment={
                                                                              "recommendations_service_host": props['recommendations_service_dns_name'],
                                                                              "offers_service_host": props['offers_service_dns_name'],
                                                                              "products_service_host": props['products_service_dns_name']
                                                                          })
        self.customize_offers_recommendations_function.add_permission("PinpointOffersPermission",
                                                           principal=iam.ServicePrincipal("pinpoint.amazonaws.com"),
                                                           source_arn=f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:*")

        """
        Pinpoint SMS Alerts Lambda
        """
        pinpoint_sms_alerts_lambda_role = iam.Role(self, "PinpointSMSAlertsLambdaExecutionRole",
                                                         assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                         inline_policies={
                                                             "root": iam.PolicyDocument(statements=[
                                                                 iam.PolicyStatement(
                                                                     actions=[
                                                                         "logs:CreateLogStream",
                                                                         "logs:PutLogEvents",
                                                                         "logs:CreateLogGroup",
                                                                         "logs:GetLogEvents",
                                                                         "mobiletargeting:*"
                                                                     ],
                                                                     resources=["*"]
                                                                 ),
                                                                 iam.PolicyStatement(
                                                                     actions=["ssm:GetParameter"],
                                                                     resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                                                 )
                                                             ])
                                                         })

        pinpoint_sms_alerts_lambda_function = lambda_.Function(self, "PinpointSMSAlertsLambda",
                                                               runtime=lambda_.Runtime.PYTHON_3_8,
                                                               description="Retail Demo Store function that opts in customers to receive sms alerts from Amazon Pinpoint",
                                                               function_name="RetailDemoStorePinpointSMSAlerts",
                                                               handler="ppinpoint-sms-alerts.lambda_handler",
                                                               timeout=Duration.seconds(900),
                                                               code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "PinpointSMSAlertsLambdaBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/pinpoint-sms-alerts.zip"),
                                                               role=pinpoint_sms_alerts_lambda_role,
                                                               environment={"pinpoint_app_id": props['pinpoint_app_id']})

        pinpoint_sns_topic_kms_key = kms.Key(self, "PinpointSnsTopicKmsKey",
                                             description="Symmetric encryption KMS key for Pinpoint SNS Topic",
                                             enable_key_rotation=True,
                                             pending_window=Duration.days(7),
                                             policy=iam.PolicyDocument(statements=[
                                                 iam.PolicyStatement(
                                                     sid="Enable IAM User Permissions",
                                                     principals=[iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root")],
                                                     actions=["kms:*"],
                                                     resources=["*"]
                                                 ),
                                                 iam.PolicyStatement(
                                                     sid="Allow Amazon Pinpoint to use this key",
                                                     principals=[iam.ServicePrincipal("sms-voice.amazonaws.com")],
                                                     actions=[
                                                         "kms:GenerateDataKey*",
                                                         "kms:Decrypt"
                                                     ],
                                                     resources=["*"]
                                                 ),
                                                 iam.PolicyStatement(
                                                     sid="Allow Amazon SNS to use this key",
                                                     principals=[iam.ServicePrincipal("sns.amazonaws.com")],
                                                     actions=[
                                                         "kms:GenerateDataKey*",
                                                         "kms:Decrypt"
                                                     ],
                                                     resources=["*"]
                                                 )
                                             ]))

        pinpoint_incoming_text_alert_sns_topic = sns.CfnTopic(self, "PinpointIncomingTextAlertsSNSTopic",
                                                              subscription=[sns.CfnTopic.SubscriptionProperty(
                                                                  endpoint=pinpoint_sms_alerts_lambda_function.function_arn,
                                                                  protocol="lambda"
                                                              )],
                                                              kms_master_key_id=pinpoint_sns_topic_kms_key.key_arn)

        pinpoint_sms_alerts_lambda_function.add_permission("PinpointSMSAlertsLambdaInvokePermission",
                                                           principal=iam.ServicePrincipal("sns.amazonaws.com"),
                                                           source_arn=pinpoint_incoming_text_alert_sns_topic.attr_topic_arn)
