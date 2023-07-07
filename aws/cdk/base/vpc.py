from aws_cdk import (
    Stack,
    Aws,
    aws_ec2 as ec2,
    CfnTag,
    Tags,
    Fn
)
from constructs import Construct

class VpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(self, "VPC",
                           ip_addresses=ec2.IpAddresses.cidr("10.215.0.0/16"))
        Tags.of(self.vpc).add("Name", props['stack_name'])

        ig = ec2.CfnInternetGateway(self, "InternetGateway",
                                    tags=[CfnTag(
                                       key="Name",
                                       value=props['stack_name'])]
                                   )

        ec2.CfnVPCGatewayAttachment(self, "InternetGatewayAttachment",
                                    vpc_id=self.vpc.vpc_id,
                                    internet_gateway_id=ig.ref)

        self.subnet1 = ec2.Subnet(self, "Subnet1",
                                  vpc_id=self.vpc.vpc_id,
                                  availability_zone=self.vpc.availability_zones[0],
                                  cidr_block="10.215.10.0/24",
                                  map_public_ip_on_launch=True)
        Tags.of(self.subnet1).add("Name", f"{props['stack_name']} (Public)")

        self.subnet2 = ec2.Subnet(self, "Subnet2",
                                  vpc_id=self.vpc.vpc_id,
                                  availability_zone=self.vpc.availability_zones[1],
                                  cidr_block="10.215.20.0/24",
                                  map_public_ip_on_launch=True)
        Tags.of(self.subnet2).add("Name", f"{props['stack_name']} (Public)")

        route_table = ec2.CfnRouteTable(self, "RouteTable",
                                        vpc_id=self.vpc.vpc_id)
        Tags.of(route_table).add("Name", props['stack_name'])

        ec2.CfnRoute(self, "DefaultRoute",
                     route_table_id=route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     gateway_id=ig.ref)

        ec2.CfnSubnetRouteTableAssociation(self, "Subnet1RouteTableAssociation",
                                           route_table_id=route_table.ref,
                                           subnet_id=self.subnet1.subnet_id)

        ec2.CfnSubnetRouteTableAssociation(self, "Subnet2RouteTableAssociation",
                                           route_table_id=route_table.ref,
                                           subnet_id=self.subnet2.subnet_id)

        ec2.CfnVPCEndpoint(self, "S3Endpoint",
                           service_name=f"com.amazonaws.{Aws.REGION}.s3",
                           vpc_id=self.vpc.vpc_id,
                           route_table_ids=[route_table.ref])
