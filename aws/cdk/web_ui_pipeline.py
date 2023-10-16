from aws_cdk import (
    Stack,
    Aws,
    Duration,
    RemovalPolicy,
    CfnTag,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    CustomResource,
    BundlingOptions
)
from constructs import Construct

class WebUIPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        copy_images_execution_role = iam.Role(self, "CopyImagesLambdaExecutionRole",
                                              assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                              inline_policies={
                                                  "LoggingPolicy": iam.PolicyDocument(statements=[
                                                      iam.PolicyStatement(
                                                          actions=[
                                                              "logs:CreateLogGroup",
                                                              "logs:CreateLogStream",
                                                              "logs:PutLogEvents"
                                                          ],
                                                          resources=["*"]
                                                      )
                                                  ]),
                                                  "S3": iam.PolicyDocument(statements=[
                                                      iam.PolicyStatement(
                                                          actions=[
                                                              "s3:List*",
                                                              "s3:PutObject",
                                                              "s3:GetObject"
                                                          ],
                                                          resources=[
                                                              f"arn:aws:s3:::{props['resource_bucket']}",
                                                              props['web_ui_bucket'].bucket_arn,
                                                              f"arn:aws:s3:::{props['resource_bucket']}/*",
                                                              f"{props['web_ui_bucket'].bucket_arn}/*"
                                                          ]
                                                      )
                                                  ])
                                              })

        copy_images_lambda_function = lambda_.Function(self, "CopyImagesLambdaFunction",
                                                       runtime=lambda_.Runtime.PYTHON_3_10,
                                                       description="Retail Demo Store deployment utility function that copies catalog images from staging bucket to Web UI bucket",
                                                       handler="index.handler",
                                                       code=lambda_.Code.from_asset("services/lambda/copy_images",
                                                                      bundling=BundlingOptions(
                                                                          image=lambda_.Runtime.PYTHON_3_10.bundling_image,
                                                                          command=[
                                                                              "bash", "-c",
                                                                              "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                                                                          ],
                                                                      )),
                                                       timeout=Duration.seconds(900),
                                                       role=copy_images_execution_role)

        CustomResource(self, "CustomCopyImagesLambdaFunction",
                       resource_type="Custom::CopyImagesToWebUI",
                       service_token=copy_images_lambda_function.function_arn,
                       properties={
                           "SourceBucket": props['resource_bucket'],
                           "SourceBucketPath": f"{props['resource_bucket_relative_path']}images",
                           "TargetBucket": props['web_ui_bucket'].bucket_name,
                           "ResourceBucketRelativePath": props['resource_bucket_relative_path']
                       })

        artifact_bucket = s3.Bucket(self, "ArtifactBucket",
                                    versioned=True,
                                    encryption=s3.BucketEncryption.KMS,
                                    bucket_key_enabled=True,
                                    removal_policy=RemovalPolicy.DESTROY,
                                    server_access_logs_bucket=props['logging_bucket'],
                                    server_access_logs_prefix="artifactui-logs")

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
                                                              "cloudfront:CreateInvalidation",
                                                              "ssm:GetParameters"
                                                          ],
                                                          resources=["*"]
                                                      )
                                                  ]),
                                                  "S3": iam.PolicyDocument(statements=[
                                                      iam.PolicyStatement(
                                                          actions=[
                                                              "s3:GetObjectVersion",
                                                              "s3:GetBucketVersioning",
                                                              "s3:PutObject",
                                                              "s3:GetObject"
                                                          ],
                                                          resources=[
                                                              artifact_bucket.bucket_arn,
                                                              f"{artifact_bucket.bucket_arn}/*",
                                                              props['web_ui_bucket'].bucket_arn,
                                                              f"{props['web_ui_bucket'].bucket_arn}/*"
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
                                                         resources=[
                                                             artifact_bucket.bucket_arn,
                                                             f"{artifact_bucket.bucket_arn}/*"
                                                         ]
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
                                              build_spec=codebuild.BuildSpec.from_asset("../../src/web-ui/buildspec.yml"),
                                              environment=codebuild.BuildEnvironment(
                                                  compute_type=codebuild.ComputeType.SMALL,
                                                  build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
                                                  environment_variables={
                                                      "PRODUCTS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "USERS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "CARTS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "VIDEOS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "ORDERS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "RECOMMENDATIONS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "SEARCH_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "LOCATION_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "OFFERS_SERVICE_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['api_gateway_url']
                                                      ),
                                                      "DEPLOYED_REGION": codebuild.BuildEnvironmentVariable(
                                                          value=Aws.REGION
                                                      ),
                                                      "PINPOINT_APP_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['pinpoint_app_id']
                                                      ),
                                                      "PERSONALIZE_TRACKING_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['parameter_personalize_event_tracker_id']
                                                      ),
                                                      "AMPLITUDE_API_KEY": codebuild.BuildEnvironmentVariable(
                                                          value=props['parameter_amplitude_api_key'].parameter_name,
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE
                                                      ),
                                                      "OPTIMIZELY_SDK_KEY": codebuild.BuildEnvironmentVariable(
                                                          value=props['parameter_optimizely_sdk_key'].parameter_name,
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE
                                                      ),
                                                      "WEB_ROOT_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['web_root_url']
                                                      ),
                                                      "IMAGE_ROOT_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['image_root_url']
                                                      ),
                                                      "COGNITO_USER_POOL_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['user_pool_id']
                                                      ),
                                                      "COGNITO_USER_POOL_CLIENT_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['user_pool_client_id']
                                                      ),
                                                      "WEB_BUCKET_NAME": codebuild.BuildEnvironmentVariable(
                                                          value=props['web_ui_bucket'].bucket_name
                                                      ),
                                                      "COGNITO_IDENTITY_POOL_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['identity_pool_id']
                                                      ),
                                                      "CLOUDFRONT_DIST_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['web_ui_cdn']
                                                      ),
                                                      "AMAZON_PAY_PUBLIC_KEY_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['amazon_pay_public_key_id']
                                                      ),
                                                      "AMAZON_PAY_STORE_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['amazon_pay_store_id']
                                                      ),
                                                      "AMAZON_PAY_MERCHANT_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['amazon_pay_merchant_id']
                                                      ),
                                                      "LOCATION_RESOURCE_NAME": codebuild.BuildEnvironmentVariable(
                                                          value=props['location_resource_name']
                                                      ),
                                                      "LOCATION_NOTIFICATION_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['location_notification_endpoint']
                                                      ),
                                                      "SEGMENT_WRITE_KEY": codebuild.BuildEnvironmentVariable(
                                                          value=props['parameter_segment_write_key'].parameter_name,
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE
                                                      ),
                                                      "GOOGLE_ANALYTICS_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['google_analytics_measurement_id'].parameter_name,
                                                          type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE
                                                      ),
                                                      "FENIX_ZIP_DETECT_URL": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_zip_detect_url']
                                                      ),
                                                      "FENIX_TENANT_ID": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_tenant_id']
                                                      ),
                                                      "FENIX_EDD_ENDPOINT": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_edd_endpoint']
                                                      ),
                                                      "FENIX_MONETARY_VALUE": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_monetary_value']
                                                      ),
                                                      "FENIX_ENABLED_PDP": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_enabled_pdp']
                                                      ),
                                                      "FENIX_ENABLED_CART": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_enabled_cart']
                                                      ),
                                                      "FENIX_ENABLED_CHECKOUT": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_enabled_checkout']
                                                      ),
                                                      "FENIX_X_API_KEY": codebuild.BuildEnvironmentVariable(
                                                          value=props['fenix_xapi_key']
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
                                                     "OAuthToken": props['github_token']
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
                                         value="web-ui"
                                     )])

        elif props['source_deployment_type'] == "CodeCommit":

            codepipeline.CfnPipeline(self, "PipelineCodeCommit",
                                     role_arn=codepipeline_service_role.role_arn,
                                     artifact_stores=[codepipeline.CfnPipeline.ArtifactStoreMapProperty(
                                         artifact_store=codepipeline.CfnPipeline.ArtifactStoreProperty(
                                             location=artifact_bucket.bucket_name,
                                             type="S3",
                                         ),
                                         region=Aws.REGION
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
                                                     "ProjectName": codebuild_project.project_name
                                                 },
                                                 run_order=1
                                             )]
                                         ),
                                     ],
                                     tags=[CfnTag(
                                         key="RetailDemoStoreServiceName",
                                         value="web-ui"
                                     )])
