from aws_cdk import (
    Stack,
    Duration,
    aws_opensearchservice as opensearchservice,
    aws_iam as iam,
    aws_ec2 as ec2
)
from constructs import Construct

class OpenSearchStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        opensearchservice_access_policy = iam.PolicyDocument(
            statements=[iam.PolicyStatement(
                actions=["es:*"],
                resources=["*"]
            )])

        self.security_group = ec2.SecurityGroup(self, "SecurityGroup",
                                                vpc=props['vpc'],
                                                description="OpenSearch Security Group")
        self.security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))

        self.domain = opensearchservice.CfnDomain(self, "OpenSearchDomain",
                                                  engine_version="OpenSearch_2.3",
                                                  cluster_config=opensearchservice.CfnDomain.ClusterConfigProperty(
                                                      dedicated_master_enabled=False,
                                                      instance_count=1,
                                                      instance_type="t3.small.search",
                                                      zone_awareness_enabled=False
                                                  ),
                                                  domain_endpoint_options=opensearchservice.CfnDomain.DomainEndpointOptionsProperty(
                                                      enforce_https=True,
                                                  ),
                                                  node_to_node_encryption_options=opensearchservice.CfnDomain.NodeToNodeEncryptionOptionsProperty(
                                                      enabled=True
                                                  ),
                                                  ebs_options=opensearchservice.CfnDomain.EBSOptionsProperty(
                                                      ebs_enabled=True,
                                                      iops=0,
                                                      volume_size=10,
                                                      volume_type="gp2"
                                                  ),
                                                  access_policies=[opensearchservice_access_policy],
                                                  advanced_options={
                                                      "rest.action.multi.allow_explicit_index": "true"
                                                  },
                                                  encryption_at_rest_options=opensearchservice.CfnDomain.EncryptionAtRestOptionsProperty(
                                                      enabled=True,
                                                  ),
                                                  vpc_options=opensearchservice.CfnDomain.VPCOptionsProperty(
                                                      security_group_ids=[self.security_group.security_group_id],
                                                      subnet_ids=[props['subnet1'].subnet_id]
                                                  ))
