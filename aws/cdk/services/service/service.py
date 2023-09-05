from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_ecs as ecs,
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
                                                  props['products_table'].attr_arn,
                                                  props['categories_table'].attr_arn,
                                                  props['experiment_strategy_table'].attr_arn,
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
                                                  resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
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
            self.task_role.attach_inline_policy(iam.Policy(self, "AmazonPaySigningLambdaInlinePolicy",
                                                           statements=[iam.PolicyStatement(
                                                               actions=["lambda:InvokeFunction"],
                                                               resources=[props['amazon_pay_signing_lambda'].function_arn]
                                                           )]
            ))

        task_definition = ecs.CfnTaskDefinition(self, "TaskDefinition",
                                                family=f"{props['stack_name']}-retaildemostore",
                                                requires_compatibilities=['FARGATE'],
                                                memory=props['container_memory'],
                                                cpu=props['container_cpu'],
                                                network_mode="awsvpc",
                                                execution_role_arn=self.task_execution_role.role_arn,
                                                task_role_arn=self.task_role.role_arn,
                                                container_definitions=[
                                                    ecs.CfnTaskDefinition.ContainerDefinitionProperty(
                                                        image="public.ecr.aws/xray/aws-xray-daemon:alpha",
                                                        name="X-ray",
                                                        port_mappings=[ecs.CfnTaskDefinition.PortMappingProperty(
                                                            container_port=2000,
                                                            protocol="udp"
                                                        )],
                                                    ),
                                                    ecs.CfnTaskDefinition.ContainerDefinitionProperty(
                                                        image=props['container_image'],
                                                        name=props['service_name'],
                                                        essential=True,
                                                        memory=256,
                                                        port_mappings=[ecs.CfnTaskDefinition.PortMappingProperty(
                                                            container_port=80
                                                        )],
                                                        log_configuration=ecs.CfnTaskDefinition.LogConfigurationProperty(
                                                            log_driver="awslogs",
                                                            options={
                                                                "awslogs-region": Aws.REGION,
                                                                "awslogs-group": props['log_group'].log_group_name,
                                                                "awslogs-stream-prefix": props['stack_name']
                                                            }
                                                        ),
                                                        secrets=[ecs.CfnTaskDefinition.SecretProperty(
                                                            name="OPTIMIZELY_SDK_KEY",
                                                            value_from=f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore-optimizely-sdk-key",
                                                        ),
                                                        ecs.CfnTaskDefinition.SecretProperty(
                                                            name="SEGMENT_WRITE_KEY",
                                                            value_from=f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore-segment-write-key",
                                                        )],
                                                        environment=[
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="PERSONALIZE_CAMPAIGN_ARN",
                                                                value=props['env_personalize_campaign_arn']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="SEARCH_CAMPAIGN_ARN",
                                                                value=props['env_personalize_search_campaign_arn']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="PRODUCTS_SERVICE_HOST",
                                                                value=props['env_products_service_internal_url']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="PRODUCTS_SERVICE_PORT",
                                                                value="80"
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="USERS_SERVICE_HOST",
                                                                value=props['env_users_service_internal_url']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="USERS_SERVICE_PORT",
                                                                value="80"
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="SEARCH_SERVICE_HOST",
                                                                value=props['env_search_service_internal_url']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="SEARCH_SERVICE_PORT",
                                                                value="80"
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="OFFERS_SERVICE_HOST",
                                                                value=props['env_offers_service_internal_url']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="OFFERS_SERVICE_PORT",
                                                                value="80"
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="STACK_BUCKET",
                                                                value=""
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="RESOURCE_BUCKET",
                                                                value=props['resource_bucket']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="PARAMETER_IVS_VIDEO_CHANNEL_MAP",
                                                                value=props['parameter_ivs_video_channel_map']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="USE_DEFAULT_IVS_STREAMS",
                                                                value=str(props['use_default_ivs_streams']),
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="OPENSEARCH_DOMAIN_HOST",
                                                                value=props['env_opensearch_domain_endpoint'],
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="OPENSEARCH_DOMAIN_PORT",
                                                                value="443"
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="DDB_TABLE_PRODUCTS",
                                                                value=props['products_table'].ref
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="DDB_TABLE_CATEGORIES",
                                                                value=props['categories_table'].ref
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="WEB_ROOT_URL",
                                                                value=props['web_root_url']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="IMAGE_ROOT_URL",
                                                                value=props['image_root_url']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="PERSONALIZE_PRECREATE_CAMPAIGNS_EVENTRULENAME",
                                                                value="RetailDemoStore-PersonalizePreCreateScheduledRule"
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="PINPOINT_APP_ID",
                                                                value=props['pinpoint_app_id']
                                                            ),
                                                            ecs.CfnTaskDefinition.KeyValuePairProperty(
                                                                name="EVIDENTLY_PROJECT_NAME",
                                                                value=props['evidently_project_name']
                                                            ),
                                                        ],
                                                    ),
                                                ])

        self.fargate_service = ecs.CfnService(self, "FargateService",
                                              cluster=props['cluster'].cluster_arn,
                                              desired_count=int(props['desired_count']),
                                              task_definition=task_definition.attr_task_definition_arn,
                                              launch_type="FARGATE",
                                              network_configuration=ecs.CfnService.NetworkConfigurationProperty(
                                                  awsvpc_configuration=ecs.CfnService.AwsVpcConfigurationProperty(
                                                      assign_public_ip="DISABLED",
                                                      security_groups=[props['source_security_group'].security_group_id],
                                                      subnets=[props['subnet1'].subnet_id, props['subnet2'].subnet_id],
                                                  )
                                              ),
                                              load_balancers=[ecs.CfnService.LoadBalancerProperty(
                                                  container_name=props['service_name'],
                                                  container_port=80,
                                                  target_group_arn=props['target_group'].attr_target_group_arn
                                              )])

        servicediscovery.CfnService(self, "ServiceDiscoveryService",
                                    dns_config=servicediscovery.CfnService.DnsConfigProperty(
                                        dns_records=[servicediscovery.CfnService.DnsRecordProperty(
                                            ttl=10,
                                            type="SRV"
                                        )]
                                    ),
                                    name=props['service_name'],
                                    namespace_id=props['service_discovery_namespace'])
