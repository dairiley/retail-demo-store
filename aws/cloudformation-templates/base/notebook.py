from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_ec2 as ec2,
    CfnTag
)
from constructs import Construct

class NotebookStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not props['github_user']:
            props['github_user'] = "aws-samples"
        sagemaker.CfnCodeRepository(self, "RetailDemoStoreGitHubRepo",
                                    code_repository_name=f"{props['uid']}-demo-store",
                                    git_config=sagemaker.CfnCodeRepository.GitConfigProperty(
                                        repository_url=f"https://github.com/{props['github_user']}/retail-demo-store.git",
                                        branch=props['github_branch']
                                    ))

        execution_role = iam.Role(self, "ExecutionRole",
                            assumed_by=iam.CompositePrincipal(
                                iam.ServicePrincipal("sagemaker.amazonaws.com"),
                                iam.ServicePrincipal("lambda.amazonaws.com"),
                            ),
                            inline_policies={
                                "Global": iam.PolicyDocument(
                                    statements=[iam.PolicyStatement(
                                    actions=[
                                        "codecommit:*",
                                        "sagemaker:ListTags",
                                        "cloudformation:DescribeStacks"
                                    ],
                                    resources=[
                                        f"arn:aws:codecommit:{Aws.REGION}:{Aws.ACCOUNT_ID}:retaildemostore*",
                                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:notebook-instance/*",
                                        f"arn:aws:cloudformation:{Aws.REGION}:{Aws.ACCOUNT_ID}:stack/{props['parent_stack_name']}*"
                                    ])]
                                ),
                                "0-StartHere": iam.PolicyDocument(
                                   statements=[iam.PolicyStatement(
                                    actions=[
                                        "servicediscovery:DiscoverInstances",
                                        "es:ListDomainNames",
                                        "es:DescribeDomain",
                                        "es:ListTags"
                                    ],
                                    resources=["*"]
                                   )]
                                ),
                                "1-Personalize": iam.PolicyDocument(
                                    statements=[
                                        iam.PolicyStatement(
                                            actions=["personalize:*"],
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
                                            actions=[
                                                "s3:PutObject",
                                                "s3:GetObject",
                                                "s3:GetObjectVersion",
                                                "s3:GetBucketVersioning",
                                                "s3:GetBucketPolicy"
                                            ],
                                            resources=[
                                                props['stack_bucket_arn'],
                                                props['resource_bucket']
                                            ]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "iam:GetRole",
                                                "iam:GetRolePolicy",
                                                "iam:PassRole"
                                            ],
                                            resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=["iam:UpdateAssumeRolePolicy"],
                                            resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/{Aws.REGION}-mParticleKinesisCrossAccountRole"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "iam:CreatePolicy",
                                                "iam:DeletePolicy"
                                            ],
                                            resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:policy/KinesismParticlePolicy"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "iam:CreateUser",
                                                "iam:DeleteUser",
                                                "iam:AttachUserPolicy",
                                                "iam:DetachUserPolicy",
                                                "iam:CreateAccessKey",
                                                "iam:DeleteAccessKey"
                                            ],
                                            resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:user/mParticleRetailDemoStoreKinesis"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "codepipeline:ListPipelines",
                                                "codepipeline:ListTagsForResource",
                                                "codepipeline:StartPipelineExecution"
                                            ],
                                            resources=[f"arn:aws:codepipeline:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "events:DescribeRule",
                                                "events:ListRules",
                                                "events:EnableRule"
                                            ],
                                            resources=[f"arn:aws:events:{Aws.REGION}:{Aws.ACCOUNT_ID}:rule/RetailDemoStore-PersonalizePreCreateScheduledRule"]
                                        )
                                    ]
                                ),
                                "3-Experimentation": iam.PolicyDocument(
                                    statements=[
                                        iam.PolicyStatement(
                                            actions=[
                                                "servicediscovery:DiscoverInstances",
                                                "elasticloadbalancing:DescribeLoadBalancers",
                                                "elasticloadbalancing:DescribeTags"
                                            ],
                                            resources=["*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=["dynamodb:*"],
                                            resources=[props['experiment_strategy_table_arn']]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "evidently:GetFeature",
                                                "evidently:EvaluateFeature",
                                                "evidently:CreateExperiment",
                                                "evidently:StartExperiment",
                                                "evidently:StopExperiment"
                                            ],
                                            resources=[f"arn:aws:evidently:{Aws.REGION}:{Aws.ACCOUNT_ID}:project/{props['evidently_project_name']}"]
                                        )
                                    ]
                                ),
                                "4-Messaging": iam.PolicyDocument(
                                    statements=[
                                        iam.PolicyStatement(
                                            actions=[
                                                "mobiletargeting:*",
                                                "iam:GetRole",
                                                "elasticloadbalancing:DescribeLoadBalancers",
                                                "elasticloadbalancing:DescribeTags"
                                            ],
                                            resources=[f"arn:aws:lambda:{Aws.REGION}:{Aws.ACCOUNT_ID}:function:RetailDemoStorePinpointRecommender"]
                                        )
                                    ]
                                ),
                                "7-Location": iam.PolicyDocument(
                                    statements=[
                                        iam.PolicyStatement(
                                            actions=[
                                                "geo:CreateMap",
                                                "geo:DeleteMap"
                                            ],
                                            resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:map*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "geo:PutGeofence",
                                                "geo:CreateGeofenceCollection",
                                                "geo:BatchDeleteGeofence",
                                                "geo:DeleteGeofenceCollection",
                                                "geo:ListGeofences",
                                                "geo:ListGeofenceCollections"
                                            ],
                                            resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:geofence-collection*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "geo:AssociateTrackerConsumer",
                                                "geo:DisassociateTrackerConsumer",
                                                "geo:CreateTracker",
                                                "geo:DeleteTracker"
                                            ],
                                            resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:tracker*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "geo:BatchUpdateDevicePosition",
                                                "geo:BatchGetDevicePosition",
                                                "geo:DescribeTracker",
                                                "geo:GetDevicePosition",
                                                "geo:GetDevicePositionHistory"
                                            ],
                                            resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:tracker/RetailDemoStoreLocationWorkshop*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "geo:GetGeofence",
                                                "geo:DescribeGeofenceCollection"
                                            ],
                                            resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:geofence-collection/RetailDemoStoreLocationWorkshop*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "events:PutRule",
                                                "events:DeleteRule",
                                                "events:PutTargets",
                                                "events:RemoveTargets"
                                            ],
                                            resources=[f"arn:aws:events:{Aws.REGION}:{Aws.ACCOUNT_ID}:rule/*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=["cognito-idp:AdminGetUser"],
                                            resources=[props['user_pool_arn']]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "lambda:AddPermission",
                                                "lambda:CreateFunction",
                                                "lambda:DeleteFunction"
                                            ],
                                            resources=[f"arn:aws:lambda:{Aws.REGION}:{Aws.ACCOUNT_ID}:function:LocationNotebookEventHandler"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "logs:CreateLogGroup",
                                                "logs:CreateLogStream",
                                                "logs:PutLogEvents"
                                            ],
                                            resources=["*"]
                                        )
                                    ]
                                )
                            })

        security_group = ec2.SecurityGroup(self, "SecurityGroup",
                                           vpc=props['vpc'],
                                           description="Notebook Instance Security Group")
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))

        self.notebook = sagemaker.CfnNotebookInstance(self, "NotebookInstance",
                                                      instance_type="ml.t3.medium",
                                                      role_arn=execution_role.role_arn,
                                                      default_code_repository=f"{props['uid']}-demo-store"']',
                                                      platform_identifier="notebook-al2-v2",
                                                      security_group_ids=[security_group.security_group_id],
                                                      subnet_id=props['subnet1'].subnet_id,
                                                      tags=[
                                                          CfnTag(
                                                              key="Uid",
                                                              value=props['uid']
                                                          ),
                                                          CfnTag(
                                                              key="PinpointAppId",
                                                              value=props['pinpoint_app_id']
                                                          ),
                                                          CfnTag(
                                                              key="UserPoolId",
                                                              value=props['user_pool_id']
                                                          )
                                                      ])
