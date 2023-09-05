from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    CustomResource
)
from constructs import Construct

class DeploymentSupportStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        Pre-Create Personalize Resources
        """

        personalize_pre_create_lambda_role = iam.Role(self, "PersonalizePreCreateLambdaExecutionRole",
                                                      assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                      inline_policies={
                                                          "root": iam.PolicyDocument(statements=[
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "logs:CreateLogStream",
                                                                      "logs:PutLogEvents",
                                                                      "logs:CreateLogGroup",
                                                                      "personalize:List*",
                                                                      "events:PutRule",
                                                                      "events:PutTargets",
                                                                      "events:RemoveTargets",
                                                                      "events:DeleteRule"
                                                                  ],
                                                                  resources=["*"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "ssm:PutParameter",
                                                                      "ssm:GetParameter"
                                                                  ],
                                                                  resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=["iam:PassRole"],
                                                                  resources=[f"arn:aws:iam::{Aws.REGION}:{Aws.ACCOUNT_ID}:role/{props['uid']})-PersonalizeS3"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "events:ListTargetsByRule",
                                                                      "events:DisableRule",
                                                                      "events:EnableRule"
                                                                  ],
                                                                  resources=[f"arn:aws:events:{Aws.REGION}:{Aws.ACCOUNT_ID}:rule/RetailDemoStore-PersonalizePreCreateScheduledRule"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "lambda:AddPermission",
                                                                      "lambda:RemovePermission"
                                                                  ],
                                                                  resources=[f"arn:aws:lambda:{Aws.REGION}:{Aws.ACCOUNT_ID}:function:RetailDemoStorePersonalizePreCreateResources"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "personalize:Create*",
                                                                      "personalize:Delete*",
                                                                      "personalize:Describe*"
                                                                  ],
                                                                  resources=[f"arn:aws:personalize:{Aws.REGION}:{Aws.ACCOUNT_ID}:*/retaildemo*"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "personalize:DescribeEventTracker",
                                                                      "personalize:DeleteEventTracker"
                                                                  ],
                                                                  resources=[f"arn:aws:personalize:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"]
                                                              ),
                                                              iam.PolicyStatement(
                                                                  actions=[
                                                                      "codepipeline:ListPipelines",
                                                                      "codepipeline:ListTagsForResource",
                                                                      "codepipeline:StartPipelineExecution"
                                                                  ],
                                                                  resources=[f"arn:aws:codepipeline:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"]
                                                              )
                                                          ])
                                                      })



        personalize_pre_create_lambda_function = lambda_.Function(self, "PersonalizePreCreateLambdaFunction",
                                                                  runtime=lambda_.Runtime.PYTHON_3_8,
                                                                  description="Retail Demo Store deployment utility function that uploads datasets, builds solutions, and creates campaigns in Amazon Personalize",
                                                                  handler="personalize_pre_create_resources.lambda_handler",
                                                                  function_name="RetailDemoStorePersonalizePreCreateResources",
                                                                  code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "PersonalizePreCreationLambdaFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/amazon-pay-signing.zip"),
                                                                  timeout=Duration.seconds(900),
                                                                  role=personalize_pre_create_lambda_role,
                                                                  environment={
                                                                      "csv_bucket": props['resource_bucket'],
                                                                      "csv_path": f"{props['resource_bucket_relative_path']}/csvs/",
                                                                      "lambda_event_rule_name": "RetailDemoStore-PersonalizePreCreateScheduledRule",
                                                                      "Uid": props['uid'],
                                                                      "DeployPersonalizedOffersCampaign": 'Yes' if props['deploy_personalized_offers_campaign'] else 'No',
                                                                      "ProductsServiceExternalUrl": props['products_service_external_url'],
                                                                      "PersonalizeRoleArn": props['personalize_role_arn'],
                                                                      "PreCreatePersonalizeResources": 'Yes' if props['pre_create_personalize_resources'] else 'No'
                                                                  })

        personalize_pre_create_scheduled_rule = events.Rule(self, "PersonalizePreCreateScheduledRule",
                                                            rule_name="RetailDemoStore-PersonalizePreCreateScheduledRule",
                                                            description="Calls Personalize pre-create Lambda function every 5 minutes until Personalize reaches desired state",
                                                            schedule=events.Schedule.rate(Duration.minutes(5)))
        personalize_pre_create_scheduled_rule.add_target(targets.LambdaFunction(personalize_pre_create_lambda_function))

        personalize_pre_create_lambda_function.add_permission("PersonalizePreCreatePermissionToInvokeLambda",
                                                              principal=iam.ServicePrincipal("events.amazonaws.com"),
                                                              source_arn=personalize_pre_create_scheduled_rule.rule_arn)

        CustomResource(self, "CustomLaunchPersonalizePreCreateLambdaFunction",
                       resource_type="Custom::CustomLambdaPersonalize",
                       service_token=personalize_pre_create_lambda_function.function_arn)

        """
        Create IVS Channels
        """

        if props['use_default_ivs_streams']:

            ivs_create_channels_lambda_role = iam.Role(self, "IVSCreateChannelsLambdaExecutionRole",
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
                                                                   actions=[
                                                                       "ssm:PutParameter",
                                                                       "ssm:GetParameter"
                                                                   ],
                                                                   resources=[
                                                                       f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "ivs:CreateChannel",
                                                                       "ivs:CreateStreamKey",
                                                                       "ivs:ListStreamKeys",
                                                                       "ivs:DeleteChannel"
                                                                   ],
                                                                   resources=[f"arn:aws:ivs:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "ivs:StopStream",
                                                                       "ivs:GetChannel"
                                                                   ],
                                                                   resources=[f"arn:aws:ivs:{Aws.REGION}:{Aws.ACCOUNT_ID}:channel/*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["ivs:DeleteStreamKey"],
                                                                   resources=[f"arn:aws:ivs:{Aws.REGION}:{Aws.ACCOUNT_ID}:stream-key/*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["s3:ListBucket"],
                                                                   resources=[f"arn:aws:s3:::{props['resource_bucket']}"]
                                                               )
                                                           ])
                                                       })

            ivs_create_channels_lambda_function = lambda_.Function(self, "IVSCreateChannelsLambdaFunction",
                                                                      runtime=lambda_.Runtime.PYTHON_3_8,
                                                                      description="Retail Demo Store deployment utility function that creates IVS channels",
                                                                      handler="ivs-create-channels.lambda_handler",
                                                                      function_name="RetailDemoStoreIVSCreateChannels",
                                                                      code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "IVSCreateChannelsLambdaFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/ivs-create-channels.zip"),
                                                                      timeout=Duration.seconds(900),
                                                                      role=ivs_create_channels_lambda_role,
                                                                      environment={
                                                                          "bucket": props['resource_bucket'],
                                                                          "videos_path": f"{props['resource_bucket_relative_path']}videos/",
                                                                          "ssm_video_channel_map_param": props['parameter_ivs_video_channel_map'],
                                                                          "Uid": props['uid']
                                                                      })

            CustomResource(self, "CustomLaunchIVSCreateChannelsLambdaFunction",
                           resource_type="Custom::CustomLambdaIVS",
                           service_token=ivs_create_channels_lambda_function.function_arn)

        """
        Pre-Index OpenSearch
        """

        if props['pre_index_opensearch']:

            opensearch_pre_index_lambda_role = iam.Role(self, "OpenSearchPreIndexLambdaExecutionRole",
                                                        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                        path="/service-role/",
                                                        inline_policies={
                                                            "root": iam.PolicyDocument(statements=[
                                                                iam.PolicyStatement(
                                                                    actions=[
                                                                        "logs:CreateLogStream",
                                                                        "logs:PutLogEvents",
                                                                        "logs:CreateLogGroup",
                                                                        "ec2:CreateNetworkInterface",
                                                                        "ec2:DeleteNetworkInterface",
                                                                        "ec2:DescribeNetworkInterfaces"
                                                                    ],
                                                                    resources=["*"]
                                                                ),
                                                                iam.PolicyStatement(
                                                                    actions=[
                                                                        "es:ESHttpDelete",
                                                                        "es:ESHttpGet",
                                                                        "es:ESHttpPost",
                                                                        "es:ESHttpPut"
                                                                    ],
                                                                    resources=[props['opensearch_domain_arn']]
                                                                )
                                                            ])
                                                        })

            opensearch_pre_index_lambda_function = lambda_.Function(self, "DeployPreIndexOpenSearch",
                                                                    runtime=lambda_.Runtime.PYTHON_3_9,
                                                                    description="Retail Demo Store deployment utility function that indexes product catalog in Amazon OpenSearch",
                                                                    handler="opensearch-pre-index.lambda_handler",
                                                                    code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "DeployPreIndexOpenSearchBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/opensearch-pre-index.zip"),
                                                                    timeout=Duration.seconds(300),
                                                                    role=opensearch_pre_index_lambda_role,
                                                                    vpc=props['vpc'],
                                                                    allow_public_subnet=True,
                                                                    vpc_subnets=ec2.SubnetSelection(subnets=[props['subnet1'], props['subnet2']]),
                                                                    security_groups=[props['opensearch_security_group']])

            CustomResource(self, "CustomLaunchOpenSearchPreIndexLambdaFunction",
                           resource_type="Custom::CustomLambdaOpenSearch",
                           service_token=opensearch_pre_index_lambda_function.function_arn,
                           properties={
                               "OpenSearchDomainEndpoint": props['opensearch_domain_endpoint'],
                               "Bucket": props['resource_bucket'],
                               "File": f"{props['resource_bucket_relative_path']}data/products.yaml"
                           })

        """
        Pre-Create Pinpoint Workshop
        """

        if props['pre_create_pinpoint_workshop']:

            pinpoint_pre_create_lambda_role = iam.Role(self, "PinpointPreCreateLambdaExecutionRole",
                                                       assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                       path="/service-role/",
                                                       inline_policies={
                                                           "root": iam.PolicyDocument(statements=[
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "logs:CreateLogStream",
                                                                       "logs:PutLogEvents",
                                                                       "logs:CreateLogGroup",
                                                                       "mobiletargeting:*"
                                                                   ],
                                                                   resources=["*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["ssm:GetParameter"],
                                                                   resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=[
                                                                       "events:ListTargetsByRule",
                                                                       "events:RemoveTargets",
                                                                       "events:DeleteRule"
                                                                   ],
                                                                   resources=[f"arn:aws:events:{Aws.REGION}:{Aws.ACCOUNT_ID}:rule/RetailDemoStore-PinpointPreCreateRule"]
                                                               ),
                                                               iam.PolicyStatement(
                                                                   actions=["iam:PassRole"],
                                                                   resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/{props['uid']}-PinptP9e"]
                                                               )
                                                           ])
                                                       })

            pinpoint_pre_create_lambda_function = lambda_.Function(self, "PinpointPreCreateLambdaFunction",
                                                                   runtime=lambda_.Runtime.PYTHON_3_8,
                                                                   description="Retail Demo Store deployment utility function that configures messaging templates, segments, and campaigns in Amazon Pinpoint",
                                                                   handler="pinpoint-auto-workshop.lambda_handler",
                                                                   code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "PinpointPreCreateLambdaFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/pinpoint-auto-workshop.zip"),
                                                                   timeout=Duration.seconds(900),
                                                                   role=pinpoint_pre_create_lambda_role,
                                                                   function_name="RetailDemoStorePinpointAutoWorkshop",
                                                                   environment={
                                                                       "pinpoint_app_id": props['pinpoint_app_id'],
                                                                       "pinpoint_recommender_arn": props['customize_recommendations_function_arn'],
                                                                       "pinpoint_offers_recommender_arn": props['customize_offers_recommendations_function_arn'],
                                                                       "pinpoint_personalize_role_arn": props['pinpoint_personalize_role_arn'],
                                                                       "email_from_address": props['pinpoint_email_from_address'],
                                                                       "email_from_name": props['pinpoint_email_from_name'],
                                                                       "lambda_event_rule_name": "RetailDemoStore-PinpointPreCreateRule",
                                                                       "DeployPersonalizedOffersCampaign": 'Yes' if props['deploy_personalized_offers_campaign'] else 'No'
                                                                   })

            if props['wait_for_offers_campaign_creation_and_deploy_pre_create_pinpoint_workshop']:

                pinpoint_pre_create_rule = events.Rule(self, "PinpointPreCreateRule",
                                                       rule_name="RetailDemoStore-PinpointPreCreateRule",
                                                       description="Calls Pinpoint workshop pre-create Lambda function when the Personalize campaign ARN SSM parameter is updated",
                                                       event_pattern=events.EventPattern(
                                                           source=["aws.ssm"],
                                                           detail={
                                                               "name": "/retaildemostore/personalize/personalized-offers-arn",
                                                               "operation": {
                                                                   "Update",
                                                                   "Create"
                                                               }
                                                           },
                                                           detail_type=["Parameter Store Change"]
                                                       ))
                pinpoint_pre_create_rule.add_target(targets.LambdaFunction(pinpoint_pre_create_lambda_function))

                pinpoint_pre_create_lambda_function.add_permission("PinpointPreCreatePermissionToInvokeLambda",
                                                                   principal=iam.ServicePrincipal("events.amazonaws.com"),
                                                                   source_arn=pinpoint_pre_create_rule.rule_arn)

            CustomResource(self, "CustomLaunchPinpointPreCreateLambdaFunction",
                           service_token=pinpoint_pre_create_lambda_function.function_arn)
