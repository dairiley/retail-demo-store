from aws_cdk import (
    Stack,
    aws_codecommit as codecommit
)
from constructs import Construct

class CodeCommitStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if props['source_deployment_type'] == "CodeCommit":
            codecommit.CfnRepository(self, "SourceRepository",
                                     repository_name="retaildemostore-src",
                                     repository_description="CodeCommit Repo for the Retail Demo Store source code",
                                     code=codecommit.CfnRepository.CodeProperty(
                                         s3=codecommit.CfnRepository.S3Property(
                                             bucket=props['resource_bucket'],
                                             key=f"{props['resource_bucket_relative_path']}source/retaildemostore-source.zip"
                                         )
                                     ))
