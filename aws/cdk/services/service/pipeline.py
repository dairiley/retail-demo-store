from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_ecr as ecr,
    aws_s3 as s3,
    RemovalPolicy,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    CfnTag,
    CustomResource
)
from constructs import Construct

class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository = ecr.Repository(self, "Repository",
                                    repository_name=f"retaildemostore/"
                                                    f"{props['service_name']}",
                                    lifecycle_rules=[ecr.LifecycleRule(
                                        rule_priority=1,
                                        description="Only keep 2 images",
                                        tag_status=ecr.TagStatus("ANY"),
                                        max_image_count=2
                                    )])

        # Deletes repository when stack is deleted
        CustomResource(self, "DeleteRepository",
                       resource_type="Custom::DeleteRepository",
                       service_token=props['delete_repository_lambda_arn'],
                       properties={
                           "RegistryId": Aws.ACCOUNT_ID,
                           "RepositoryName": repository.repository_name
                       })

        artifact_bucket = s3.Bucket(self, "ArtifactBucket",
                                    versioned=True,
                                    encryption=s3.BucketEncryption.KMS,
                                    bucket_key_enabled=True,
                                    removal_policy=RemovalPolicy.DESTROY,
                                    server_access_logs_bucket=props['logging_bucket'],
                                    server_access_logs_prefix=f"/{props['fargate_service_name']}-logs")

        # Empties bucket when stack is deleted
        CustomResource(self, "EmptyArtifactBucket",
                       resource_type="Custom::EmptyArtifactBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties = {"BucketName": artifact_bucket.bucket_name})

        codebuild_service_role = iam.Role(self, "CodeBuildServiceRole",
                            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
                            inline_policies={
                                "logs": iam.PolicyDocument(
                                   statements=[iam.PolicyStatement(
                                    actions=[
                                        "logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents",
                                        "ecr:GetAuthorizationToken",
                                        "ssm:GetParameters"
                                    ],
                                    resources=["*"])]
                                ),
                                "ecr": iam.PolicyDocument(
                                    statements=[iam.PolicyStatement(
                                    actions=[
                                        "ecr:GetDownloadUrlForLayer",
                                        "ecr:BatchGetImage",
                                        "ecr:BatchCheckLayerAvailability",
                                        "ecr:PutImage",
                                        "ecr:InitiateLayerUpload",
                                        "ecr:UploadLayerPart",
                                        "ecr:CompleteLayerUpload"
                                    ],
                                    resources=[f"arn:aws:ecr:{Aws.REGION}:{Aws.ACCOUNT_ID}:repository/{repository.repository_name}"])]
                                ),
                                "S3": iam.PolicyDocument(
                                    statements=[iam.PolicyStatement(
                                        actions=[
                                            "s3:GetObject",
                                            "s3:PutObject",
                                            "s3:GetObjectVersion"
                                        ],
                                        resources=[artifact_bucket.bucket_arn])]
                                ),
                            })

        codepipeline_service_role = iam.Role(self, "CodePipelineServiceRole",
                            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
                            inline_policies={
                                "root": iam.PolicyDocument(
                                    statements=[
                                        iam.PolicyStatement(
                                            actions=[
                                                "s3:GetObject",
                                                "s3:PutObject",
                                                "s3:GetObjectVersion",
                                                "s3:GetBucketVersioning"
                                            ],
                                            resources=[artifact_bucket.bucket_arn]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "codebuild:StartBuild",
                                                "codebuild:BatchGetBuilds"
                                            ],
                                            resources=["*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=["iam:PassRole"],
                                            resources=[
                                                props['task_execution_role'].role_arn,
                                                props['task_role'].role_arn
                                            ]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "codecommit:GetBranch",
                                                "codecommit:GetCommit",
                                                "codecommit:UploadArchive",
                                                "codecommit:GetUploadArchiveStatus",
                                                "codecommit:CancelUploadArchive"
                                            ],
                                            resources=["*"]
                                        ),
                                        iam.PolicyStatement(
                                            actions=[
                                                "ecs:List*",
                                                "ecs:Describe*",
                                                "ecs:RegisterTaskDefinition",
                                                "ecs:UpdateService"
                                            ],
                                            resources=["*"]
                                        )
                                    ]
                                ),
                                "ecr": iam.PolicyDocument(
                                    statements=[iam.PolicyStatement(
                                    actions=[
                                        "ecr:GetDownloadUrlForLayer",
                                        "ecr:BatchGetImage",
                                        "ecr:BatchCheckLayerAvailability",
                                        "ecr:PutImage",
                                        "ecr:InitiateLayerUpload",
                                        "ecr:UploadLayerPart",
                                        "ecr:CompleteLayerUpload"
                                    ],
                                    resources=[f"arn:aws:ecr:{Aws.REGION}:{Aws.ACCOUNT_ID}:repository/{repository.repository_name}"])]
                                ),
                                "S3": iam.PolicyDocument(
                                    statements=[iam.PolicyStatement(
                                        actions=[
                                            "s3:GetObject",
                                            "s3:PutObject",
                                            "s3:GetObjectVersion"
                                        ],
                                        resources=[artifact_bucket.bucket_arn])]
                                ),
                            })

        codebuild_project = codebuild.Project(self, "CodeBuildProject",
                                              role=codebuild_service_role,
                                              project_name=props['stack_name'],
                                              build_spec=codebuild.BuildSpec.from_asset(f"../../{props['service_path']}/buildspec.yml"),
                                              environment=codebuild.BuildEnvironment(
                                                  compute_type=codebuild.ComputeType.SMALL,
                                                  build_image=codebuild.LinuxBuildImage.from_docker_registry("aws/codebuild/docker:17.09.0"),
                                                  environment_variables={
                                                      "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                                                          value=Aws.REGION
                                                      ),
                                                      "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                                                          value=repository.repository_arn
                                                      ),
                                                      "SERVICE_PATH": codebuild.BuildEnvironmentVariable(
                                                          value=props['service_path']
                                                      ),
                                                      "SERVICE_NAME": codebuild.BuildEnvironmentVariable(
                                                          value=props['service_name']
                                                      ),
                                                      "COGNITO_USER_POOL_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['user_pool_id']
                                                      ),
                                                      "COGNITO_USER_POOL_CLIENT_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['user_pool_client_id']
                                                      ),
                                                      "COGNITO_IDENTITY_POOL_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['identity_pool_id']
                                                      ),
                                                      "PRODUCTS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['products_service_external_url']
                                                      ),
                                                      "USERS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['users_service_external_url']
                                                      ),
                                                      "CARTS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['carts_service_external_url']
                                                      ),
                                                      "VIDEOS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['videos_service_external_url']
                                                      ),
                                                      "ORDERS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['orders_service_external_url']
                                                      ),
                                                      "RECOMMENDATIONS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['recommendations_service_external_url']
                                                      ),
                                                      "SEARCH_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['search_service_external_url']
                                                      ),
                                                      "DEPLOYED_REGION": codebuild.BuildEnvironmentVariable(
                                                          value=Aws.REGION
                                                      ),
                                                      "PINPOINT_APP_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['pinpoint_app_id']
                                                      ),
                                                      "PERSONALIZE_TRACKING_ID": codebuild.BuildEnvironmentVariable(
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                                                          value=props['parameter_personalize_event_tracker_id']
                                                      ),
                                                      "AMPLITUDE_API_KEY": codebuild.BuildEnvironmentVariable(
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                                                          value=props['parameter_amplitude_api_key']
                                                      ),
                                                      "OPTIMIZELY_SDK_KEY": codebuild.BuildEnvironmentVariable(
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                                                          value=props['parameter_optimizely_sdk_key']
                                                      ),
                                                      "WEB_ROOT_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['web_root_url']
                                                      ),
                                                      "IMAGE_ROOT_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['image_root_url']
                                                      ),
                                                  }
                                              ))

        if props['github_user']:
            codepipeline.CfnPipeline(self, "PipelineGitHub",
                                     role_arn=codepipeline_service_role.role_arn,
                                     artifact_stores=[codepipeline.CfnPipeline.ArtifactStoreMapProperty(
                                         region=Aws.REGION,
                                         artifact_store=codepipeline.CfnPipeline.ArtifactStoreProperty(
                                             location=artifact_bucket.bucket_name,
                                             type="S3",
                                         ),
                                     )],
                                     stages=[
                                         codepipeline.CfnPipeline.StageDeclarationProperty(
                                             name="Source",
                                             actions=[codepipeline.CfnPipeline.ActionDeclarationProperty(
                                                 action_type_id=codepipeline.CfnPipeline.ActionTypeIdProperty(
                                                     category="Source",
                                                     owner="ThirdParty",
                                                     provider="GitHub",
                                                     version="1"
                                                 ),
                                                 name="App",
                                                 output_artifacts=[codepipeline.CfnPipeline.OutputArtifactProperty(
                                                     name="App"
                                                 )],
                                                 configuration={
                                                     "Owner": props['github_user'],
                                                     "Repo": props['github_repo'],
                                                     "Branch": props['github_branch'],
                                                     "oauth_token": props['github_token']
                                                 },
                                                 run_order=1
                                             )]
                                         ),
                                         codepipeline.CfnPipeline.StageDeclarationProperty(
                                             name="Build",
                                             actions=[codepipeline.CfnPipeline.ActionDeclarationProperty(
                                                 action_type_id=codepipeline.CfnPipeline.ActionTypeIdProperty(
                                                     category="Build",
                                                     owner="AWS",
                                                     provider="CodeBuild",
                                                     version="1"
                                                 ),
                                                 name="Build",
                                                 input_artifacts=[codepipeline.CfnPipeline.InputArtifactProperty(
                                                     name="App"
                                                 )],
                                                 output_artifacts=[codepipeline.CfnPipeline.OutputArtifactProperty(
                                                     name="BuildOutput"
                                                 )],
                                                 configuration={
                                                     "ProjectName": codebuild_project.project_name
                                                 },
                                                 run_order=1
                                             )]
                                         ),
                                         codepipeline.CfnPipeline.StageDeclarationProperty(
                                             name="Deploy",
                                             actions=[codepipeline.CfnPipeline.ActionDeclarationProperty(
                                                 action_type_id=codepipeline.CfnPipeline.ActionTypeIdProperty(
                                                     category="Deploy",
                                                     owner="AWS",
                                                     provider="ECS",
                                                     version="1"
                                                 ),
                                                 name="Deploy",
                                                 input_artifacts=[codepipeline.CfnPipeline.InputArtifactProperty(
                                                     name="BuildOutput"
                                                 )],
                                                 configuration={
                                                     "ClusterName": props['cluster_name'],
                                                     "ServiceName": props['fargate_service_name'],
                                                     "FileName": "images.json"
                                                 },
                                                 run_order=1
                                             )]
                                         )
                                     ],
                                     tags=[CfnTag(
                                         key="RetailDemoStoreServiceName",
                                         value=props['service_name']
                                     )])

        elif props['source_deployment_type'] == "CodeCommit":
            codepipeline.CfnPipeline(self, "PipelineCodeCommit",
                                     role_arn=codepipeline_service_role.role_arn,
                                     artifact_stores=[codepipeline.CfnPipeline.ArtifactStoreMapProperty(
                                         artifact_store=codepipeline.CfnPipeline.ArtifactStoreProperty(
                                             location=artifact_bucket.ref,
                                             type="S3",
                                         ),
                                     )],
                                     stages=[
                                         codepipeline.CfnPipeline.StageDeclarationProperty(
                                             name="Source",
                                             actions=[codepipeline.CfnPipeline.ActionDeclarationProperty(
                                                 action_type_id=codepipeline.CfnPipeline.ActionTypeIdProperty(
                                                     category="Source",
                                                     owner="AWS",
                                                     provider="CodeCommit",
                                                     version="1"
                                                 ),
                                                 name="App",
                                                 output_artifacts=[codepipeline.CfnPipeline.OutputArtifactProperty(
                                                     name="App"
                                                 )],
                                                 configuration={
                                                     "RepositoryName": "retaildemostore-src",
                                                     "BranchName": "main",
                                                     "PollForSourceChanges": True
                                                 },
                                                 run_order=1
                                             )]
                                         ),
                                         codepipeline.CfnPipeline.StageDeclarationProperty(
                                             name="Build",
                                             actions=[codepipeline.CfnPipeline.ActionDeclarationProperty(
                                                 action_type_id=codepipeline.CfnPipeline.ActionTypeIdProperty(
                                                     category="Build",
                                                     owner="AWS",
                                                     provider="CodeBuild",
                                                     version="1"
                                                 ),
                                                 name="Build",
                                                 input_artifacts=[codepipeline.CfnPipeline.InputArtifactProperty(
                                                     name="App"
                                                 )],
                                                 output_artifacts=[codepipeline.CfnPipeline.OutputArtifactProperty(
                                                     name="BuildOutput"
                                                 )],
                                                 configuration={
                                                     "ProjectName": codebuild_project.ref
                                                 },
                                                 run_order=1
                                             )]
                                         ),
                                         codepipeline.CfnPipeline.StageDeclarationProperty(
                                             name="Deploy",
                                             actions=[codepipeline.CfnPipeline.ActionDeclarationProperty(
                                                 action_type_id=codepipeline.CfnPipeline.ActionTypeIdProperty(
                                                     category="Deploy",
                                                     owner="AWS",
                                                     provider="ECS",
                                                     version="1"
                                                 ),
                                                 name="Deploy",
                                                 input_artifacts=[codepipeline.CfnPipeline.InputArtifactProperty(
                                                     name="BuildOutput"
                                                 )],
                                                 configuration={
                                                     "ClusterName": props['cluster_name'],
                                                     "ServiceName": props['fargate_service_name'],
                                                     "FileName": "images.json"
                                                 },
                                                 run_order=1
                                             )]
                                         )
                                     ],
                                     tags=[CfnTag(
                                         key="RetailDemoStoreServiceName",
                                         value=props['service_name']
                                     )])
