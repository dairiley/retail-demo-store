from aws_cdk import (
    Stack,
    Aws,
    RemovalPolicy,
    CfnTag,
    aws_s3 as s3,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    CustomResource
)
from constructs import Construct

class SwaggerUIPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        artifact_bucket = s3.Bucket(self, "ArtifactBucket",
                                    versioned=True,
                                    encryption=s3.BucketEncryption.KMS,
                                    bucket_key_enabled=True,
                                    removal_policy=RemovalPolicy.DESTROY,
                                    server_access_logs_bucket=props['logging_bucket'],
                                    server_access_logs_prefix="swaggerui-logs")

        # Empties bucket when stack is deleted
        CustomResource(self, "EmptyArtifactBucket",
                       resource_type="Custom::EmptyArtifactBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties={"BucketName": artifact_bucket.bucket_name})

        codebuild_service_role = iam.Role(self, "CodeBuildServiceRole",
                                          assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
                                          inline_policies={
                                              "logs": iam.PolicyDocument(statements=[
                                                  iam.PolicyStatement(
                                                      actions=[
                                                          "logs:CreateLogGroup",
                                                          "logs:CreateLogStream",
                                                          "logs:PutLogEvents",
                                                          "ssm:GetParameters"
                                                      ],
                                                      resources=["*"]
                                                  )
                                              ]),
                                              "invalidation": iam.PolicyDocument(statements=[
                                                  iam.PolicyStatement(
                                                      actions=[
                                                          "cloudfront:CreateInvalidation",
                                                          "cloudfront:GetInvalidation"
                                                      ],
                                                      resources=[f"arn:aws:cloudfront::{Aws.ACCOUNT_ID}:distribution/{props['swagger_ui_cdn']}"]
                                                  )
                                              ]),
                                              "S3": iam.PolicyDocument(statements=[
                                                  iam.PolicyStatement(
                                                      actions=[
                                                          "s3:GetObject",
                                                          "s3:PutObject",
                                                          "s3:GetObjectVersion",
                                                          "s3:GetBucketVersioning"
                                                      ],
                                                      resources=[
                                                          artifact_bucket.bucket_arn,
                                                          props['swagger_ui_bucket_arn']
                                                      ]
                                                  )
                                              ])
                                          })

        codepipeline_service_role = iam.Role(self, "CodePipelineServiceRole",
                                             assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
                                             inline_policies={
                                                 "root": iam.PolicyDocument(statements=[
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
                                                         actions=[
                                                             "codecommit:GetBranch",
                                                             "codecommit:GetCommit",
                                                             "codecommit:UploadArchive",
                                                             "codecommit:GetUploadArchiveStatus",
                                                             "codecommit:CancelUploadArchive"
                                                         ],
                                                         resources=[f"arn:aws:codecommit:{Aws.REGION}:{Aws.ACCOUNT_ID}:retaildemostore-src"]
                                                     )
                                                 ])
                                             })

        codebuild_project = codebuild.Project(self, "CodeBuildProject",
                                              role=codebuild_service_role,
                                              description=f"Building stage for {props['stack_name']}",
                                              build_spec=codebuild.BuildSpec.from_asset("../../src/swagger-ui/buildspec.yml"),
                                              environment=codebuild.BuildEnvironment(
                                                  compute_type=codebuild.ComputeType.SMALL,
                                                  build_image=codebuild.LinuxBuildImage.STANDARD_2_0,
                                                  environment_variables={
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
                                                      "LOCATION_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['location_service_external_url']
                                                      ),
                                                      "OFFERS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['offers_service_external_url']
                                                      ),
                                                      "DEPLOYED_REGION": codebuild.BuildEnvironmentVariable(
                                                          value=Aws.REGION
                                                      ),
                                                      "SWAGGER_UI_BUCKET_NAME": codebuild.BuildEnvironmentVariable(
                                                          value=props['swagger_ui_bucket_name']
                                                      ),
                                                      "CLOUDFRONT_DIST_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['swagger_ui_cdn']
                                                      ),
                                                      "SWAGGER_UI_ROOT_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['swagger_ui_root_url']
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
                                                 name="Build-and-Deploy",
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
                                         )
                                     ],
                                     tags=[CfnTag(
                                         key="RetailDemoStoreServiceName",
                                         value="swagger-ui"
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
                                                 name="Build-and-Deploy",
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
                                     ],
                                     tags=[CfnTag(
                                         key="RetailDemoStoreServiceName",
                                         value="swagger-ui"
                                     )])

