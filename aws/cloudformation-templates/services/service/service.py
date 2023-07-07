from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_logs as logs,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_servicediscovery as servicediscovery
)
from constructs import Construct

class ServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.task_execution_role = iam.Role(self, "TaskExecutionRole",
                                           assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                           managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "AmazonECSTaskExecutionRolePolicy",
                                               managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy")],
                                           inline_policies={
                                               "ReadRetailDemoStoreSSMParams": iam.PolicyDocument(
                                                   statements=[iam.PolicyStatement(
                                                   actions=["ssm:GetParameters"],
                                                   resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"])]
                                               )
                                           })

        self.task_role = iam.Role(self, "TaskRole",
                                  assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                  managed_policies=[
                                      iam.ManagedPolicy.from_managed_policy_arn(self, "AWSCloudMapDiscoverInstanceAccess",
                                          "arn:aws:iam::aws:policy/AWSCloudMapDiscoverInstanceAccess"),
                                      iam.ManagedPolicy.from_managed_policy_arn(self, "AWSXRayDaemonWriteAccess",
                                          "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess")
                                  ],
                                  inline_policies={
                                      "DynamoDB": iam.PolicyDocument(
                                          statements=[iam.PolicyStatement(
                                              actions=["dynamodb:*"],
                                              resources=[
                                                  props['products_table'].ref,
                                                  props['categories_table'].ref,
                                                  props['experiment_strategy_table'].ref,
                                              ]
                                          )]
                                      ),
                                      "PinpointSMS": iam.PolicyDocument(
                                          statements=[
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "mobiletargeting:SendMessages",
                                                      "mobiletargeting:GetEndpoint",
                                                      "mobiletargeting:UpdateEndpoint",
                                                      "mobiletargeting:PutEvents"
                                                  ],
                                                  resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=["mobiletargeting:PhoneNumberValidate"],
                                                  resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:phone/number/validate"]
                                              )
                                          ]
                                      ),
                                      "others": iam.PolicyDocument(
                                          statements=[
                                              iam.PolicyStatement(
                                                  actions=["ssm:*"],
                                                  resources=[f"'arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "logs:CreateLogGroup",
                                                      "logs:CreateLogStream",
                                                      "logs:PutLogEvents"
                                                  ],
                                                  resources=["*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "personalize:CreateSchema",
                                                      "personalize:CreateDatasetGroup",
                                                      "personalize:CreateSolutionVersion",
                                                      "personalize:CreateDatasetImportJob",
                                                      "personalize:CreateSolution",
                                                      "personalize:DescribeDatasetGroup",
                                                      "personalize:DescribeDatasetImportJob",
                                                      "personalize:DescribeSolution",
                                                      "personalize:DescribeSolutionVersion",
                                                      "personalize:DescribeEventTracker",
                                                      "personalize:DescribeCampaign",
                                                      "personalize:DescribeRecommender",
                                                      "personalize:CreateCampaign",
                                                      "personalize:CreateDataset",
                                                      "personalize:CreateEventTracker",
                                                      "personalize:CreateFilter",
                                                      "personalize:GetPersonalizedRanking",
                                                      "personalize:GetRecommendations",
                                                      "personalize:DeleteEventTracker",
                                                      "personalize:DescribeEventTracker"
                                                  ],
                                                  resources=[f"arn:aws:personalize:{Aws.REGION}:{Aws.ACCOUNT_ID}:*/retaildemo*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "personalize:ListCampaigns",
                                                      "personalize:ListDatasetGroups",
                                                      "personalize:ListSolutions",
                                                      "personalize:ListSchemas",
                                                      "personalize:ListSolutionVersions",
                                                      "personalize:ListDatasetImportJobs",
                                                      "personalize:ListDatasets",
                                                      "personalize:ListEventTrackers"
                                                  ],
                                                  resources=["*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=["s3:GetObject"],
                                                  resources=[f"arn:aws:s3:::{props['resource_bucket']}"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=["ivs:ListStreamKeys"],
                                                  resources=[f"arn:aws:ivs:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "ivs:GetChannel",
                                                      "ivs:GetStream",
                                                      "ivs:PutMetadata"
                                                  ],
                                                  resources=[f"arn:aws:ivs:{Aws.REGION}:{Aws.ACCOUNT_ID}:channel/*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=["ivs:GetStreamKey"],
                                                  resources=[f"arn:aws:ivs:{Aws.REGION}:{Aws.ACCOUNT_ID}:stream-key/*"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "events:DescribeRule",
                                                      "events:ListRules",
                                                      "events:EnableRule"
                                                  ],
                                                  resources=[f"arn:aws:events:{Aws.REGION}:{Aws.ACCOUNT_ID}:rule/RetailDemoStore-PersonalizePreCreateScheduledRule"]
                                              ),
                                              iam.PolicyStatement(
                                                  actions=[
                                                      "evidently:BatchEvaluateFeature",
                                                      "evidently:PutProjectEvents"
                                                  ],
                                                  resources=[props['evidently_project_arn']]
                                              )
                                          ]
                                      ),
                                  })
        if props['amazon_pay_signing_lambda']:
            self.task_role.attach_inline_policy(iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[props['amazon_pay_signing_lambda'].function_arn]
            ))

        log_group = logs.LogGroup(self, "LogGroup",
                                  log_group_name=f"/ecs/{props['stack_name']}")

        task_definition = ecs.TaskDefinition(self, "TaskDefinition",
                                             family=f"{props['stack_name']}-retaildemostore",
                                             compatibility=ecs.Compatibility.FARGATE,
                                             memory_mib=props['container_memory'],
                                             cpu=props['container_cpu'],
                                             network_mode=ecs.NetworkMode.AWS_VPC,
                                             task_role=self.task_role,
                                             execution_role=self.task_execution_role)
        task_definition.add_container("X-ray",
                                      image=ecs.ContainerImage.from_registry("public.ecr.aws/xray/aws-xray-daemon:alpha"),
                                      port_mappings=[ecs.PortMapping(
                                          container_port=2000,
                                          protocol=ecs.Protocol.UDP
                                      )])

        task_definition.add_container(props['service_name'],
                                      image=ecs.ContainerImage.from_registry(props['container_image']),
                                      essential=True,
                                      memory_limit_mib=256,
                                      secrets={
                                          "OPTIMIZELY_SDK_KEY": ecs.Secret.from_ssm_parameter(ssm.StringParameter.from_string_parameter_attributes(self, "OPTIMIZELY_SDK_KEY", parameter_name="retaildemostore-optimizely-sdk-key")),
                                          "SEGMENT_WRITE_KEY": ecs.Secret.from_ssm_parameter(ssm.StringParameter.from_string_parameter_attributes(self, "SEGMENT_WRITE_KEY", parameter_name="retaildemostore-segment-write-key"))
                                      },
                                      environment={
                                          "PERSONALIZE_CAMPAIGN_ARN": props['env_personalize_campaign_arn'],
                                          "SEARCH_CAMPAIGN_ARN": props['env_personalize_search_campaign_arn'],
                                          "PRODUCTS_SERVICE_HOST": props['env_products_service_internal_url'],
                                          "PRODUCTS_SERVICE_PORT": "80",
                                          "USERS_SERVICE_HOST": props['env_users_service_internal_url'],
                                          "USERS_SERVICE_PORT": "80",
                                          "SEARCH_SERVICE_HOST": props['env_search_service_internal_url'],
                                          "SEARCH_SERVICE_PORT": "80",
                                          "OFFERS_SERVICE_HOST": props['env_offers_service_internal_url'],
                                          "OFFERS_SERVICE_PORT": "80",
                                          "STACK_BUCKET": "",
                                          "RESOURCE_BUCKET": props['resource_bucket'],
                                          "PARAMETER_IVS_VIDEO_CHANNEL_MAP": props['parameter_ivs_video_channel_map'],
                                          "USE_DEFAULT_IVS_STREAMS": str(props['use_default_ivs_streams']),
                                          "OPENSEARCH_DOMAIN_HOST": props['env_opensearch_domain_endpoint'],
                                          "OPENSEARCH_DOMAIN_PORT": "443",
                                          "DDB_TABLE_PRODUCTS": props['products_table'].ref,
                                          "DDB_TABLE_CATEGORIES": props['categories_table'].ref,
                                          "WEB_ROOT_URL": props['web_root_url'],
                                          "IMAGE_ROOT_URL": props['image_root_url'],
                                          "PERSONALIZE_PRECREATE_CAMPAIGNS_EVENTRULENAME": "RetailDemoStore-PersonalizePreCreateScheduledRule",
                                          "PINPOINT_APP_ID": props['pinpoint_app_id'],
                                          "EVIDENTLY_PROJECT_NAME": props['evidently_project_name']
                                      },
                                      port_mappings=[ecs.PortMapping(
                                          container_port=80,
                                      )],
                                      logging=ecs.LogDrivers.aws_logs(
                                          log_group=log_group,
                                          stream_prefix=props['stack_name']
                                      ))

        self.fargate_service = ecs.FargateService(self, "FargateService",
                                                  cluster=props['cluster'],
                                                  desired_count=int(props['desired_count']),
                                                  task_definition=task_definition,
                                                  security_groups=[props['source_security_group']],
                                                  vpc_subnets=ec2.SubnetSelection(subnets=[props['subnet1'], props['subnet2']]),
                                                  assign_public_ip=True)

        servicediscovery.CfnService(self, "ServiceDiscoveryService",
                                    dns_config=servicediscovery.CfnService.DnsConfigProperty(
                                        dns_records=[servicediscovery.CfnService.DnsRecordProperty(
                                            ttl=10,
                                            type="SRV"
                                        )],
                                        namespace_id="namespaceId",
                                        routing_policy="routingPolicy"
                                    ),
                                    health_check_config=servicediscovery.CfnService.HealthCheckConfigProperty(type="HTTP", failure_threshold=1),
                                    name=props['service_name'],
                                    namespace_id=props['service_discovery_namespace'])
