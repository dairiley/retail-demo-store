from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_kinesis as kinesis,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_s3 as s3
)
from constructs import Construct

class MParticleStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        kinesis.Stream(self, "mParticlePersonalizeEventsKinesisStream",
                       stream_name=f"{props['uid']}-mPEventsStream",
                       encryption=kinesis.StreamEncryption.KMS,
                       encryption_key="alias/aws/kinesis",
                       shard_count=1)

        iam.Role(self, "mParticleKinesisCrossAccountRole",
                 assumed_by=iam.ServicePrincipal("iam.amazonaws.com"),
                 role_name=f"{props['uid']}-mPKinesisRole",
                 description="Allows mParticle to write messages to your Kinesis stream",
                 managed_policies=[iam.ManagedPolicy.from_managed_policy_arn("arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole")],
                 inline_policies={
                     "root": iam.PolicyDocument(statements=[iam.PolicyStatement(
                         actions=["kinesis:PutRecord"],
                         resources=[f"arn:aws:kinesis:{Aws.REGION}:{Aws.ACCOUNT_ID}:stream/{props['uid']}-mParticlePersonalizeEventsKinesisStream"]
                     )])
                 })

        mparticle_personalize_lambda_role = iam.Role(self, "mParticlePersonalizeLambdaExecutionRole",
                                                     assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                     description="Execution role for the Lambda provided with the mParticle workshop",
                                                     managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(self, "mParticlePersonalizeLambdaExecutionRoleKinesisPolicy",
                                                                                                                 managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole"),
                                                                       iam.ManagedPolicy.from_managed_policy_arn(self, "mParticlePersonalizeLambdaExecutionRoleVPCAccess",
                                                                                                                 managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole")],
                                                     inline_policies={
                                                         "root": iam.PolicyDocument(statements=[
                                                             iam.PolicyStatement(
                                                                 actions=[
                                                                     "logs:CreateLogStream",
                                                                     "logs:PutLogEvents",
                                                                     "logs:CreateLogGroup",
                                                                     "personalize:GetRecommendations",
                                                                     "personalize:PutEvents"
                                                                 ],
                                                                 resources=["*"]
                                                             ),
                                                             iam.PolicyStatement(
                                                                 actions=[
                                                                     "ssm:GetParameter",
                                                                     "ssm:GetParameters"
                                                                 ],
                                                                 resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                                             )
                                                         ])
                                                     })

        lambda_.Function(self, "mParticlePersonalizeLambda",
                         runtime=lambda_.Runtime.NODEJS_12_X,
                         description="Handles sending events passed from mParticle to the Personalize tracker for user-item interactions",
                         function_name=f"{props['uid']}-mPEventsLambda",
                         handler="mparticle-personalize.handler",
                         code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "mParticlePersonalizeLambdaBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/mparticle-personalize.zip"),
                         timeout=Duration.seconds(900),
                         vpc=props['vpc'],
                         allow_public_subnet=True,
                         vpc_subnets=ec2.SubnetSelection(subnets=[props['private_subnet1'], props['private_subnet2']]),
                         role=mparticle_personalize_lambda_role)

