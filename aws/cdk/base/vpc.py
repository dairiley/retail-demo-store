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

        self.vpc_cidr = "10.215.0.0/16"
        self.vpc = ec2.Vpc(self, "VPC",
                           ip_addresses=ec2.IpAddresses.cidr("10.215.0.0/16"),
                           enable_dns_hostnames=True,
                           enable_dns_support=True,
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   name="PublicSubnet1",
                                   cidr_mask=24,
                                   subnet_type=ec2.SubnetType.PUBLIC
                               ),
                               ec2.SubnetConfiguration(
                                   name="PublicSubnet2",
                                   cidr_mask=24,
                                   subnet_type=ec2.SubnetType.PUBLIC
                               ),
                               ec2.SubnetConfiguration(
                                   name="PrivateSubnet1",
                                   cidr_mask=24,
                                   subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                               ),
                               ec2.SubnetConfiguration(
                                   name="PrivateSubnet2",
                                   cidr_mask=24,
                                   subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                               )
                           ])
        Tags.of(self.vpc).add("Name", props['stack_name'])

        """
        Public Subnet 1
        """

        self.public_subnet_1 = ec2.Subnet(self, "PublicSubnet1",
                                          vpc_id=self.vpc.vpc_id,
                                          availability_zone=self.vpc.availability_zones[0],
                                          cidr_block="10.215.30.0/24",
                                          map_public_ip_on_launch=True)
        Tags.of(self.public_subnet_1).add("Name", f"{props['stack_name']}/VPC/PublicSubnet1")

        """
        Public Subnet 1
        """

        self.public_subnet_2 = ec2.Subnet(self, "PublicSubnet2",
                                          vpc_id=self.vpc.vpc_id,
                                          availability_zone=self.vpc.availability_zones[1],
                                          cidr_block="10.215.40.0/24",
                                          map_public_ip_on_launch=True)
        Tags.of(self.public_subnet_2).add("Name", f"{props['stack_name']}/VPC/PublicSubnet2")

        public_route_table = ec2.CfnRouteTable(self, "PublicRouteTable",
                                               vpc_id=self.vpc.vpc_id)
        Tags.of(public_route_table).add("Name", f"{props['stack_name']}/VPC/PublicRouteTable")

        ec2.CfnRoute(self, "PublicDefaultRoute",
                     route_table_id=public_route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     gateway_id=self.vpc.internet_gateway_id)

        public_subnet_1_eip = ec2.CfnEIP(self, "PublicSubnet1EIP",
                                         domain="vpc",
                                         tags=[CfnTag(
                                             key="Name",
                                             value=f"{props['stack_name']}/VPC/PublicSubnet1EIP"
                                         )])

        public_subnet_1_nat_gateway = ec2.CfnNatGateway(self, "PublicSubnet1NATGateway",
                                                        subnet_id=self.public_subnet_1.subnet_id,
                                                        allocation_id=public_subnet_1_eip.attr_allocation_id,
                                                        tags=[CfnTag(
                                                            key="Name",
                                                            value=f"{props['stack_name']}/VPC/NatGateway1"
                                                        )])

        public_subnet_2_eip = ec2.CfnEIP(self, "PublicSubnet2EIP",
                                         domain="vpc",
                                         tags=[CfnTag(
                                             key="Name",
                                             value=f"{props['stack_name']}/VPC/PublicSubnet2EIP"
                                         )])

        public_subnet_2_nat_gateway = ec2.CfnNatGateway(self, "PublicSubnet2NATGateway",
                                                        subnet_id=self.public_subnet_2.subnet_id,
                                                        allocation_id=public_subnet_2_eip.attr_allocation_id,
                                                        tags=[CfnTag(
                                                            key="Name",
                                                            value=f"{props['stack_name']}/VPC/NatGateway2"
                                                        )])

        """
        Private Subnet 1
        """

        self.private_subnet_1 = ec2.Subnet(self, "PrivateSubnet1",
                                  vpc_id=self.vpc.vpc_id,
                                  availability_zone=self.vpc.availability_zones[0],
                                  cidr_block="10.215.10.0/24",
                                  map_public_ip_on_launch=False)
        Tags.of(self.private_subnet_1).add("Name", f"{props['stack_name']}/VPC/PrivateSubnet1")

        private_subnet_1_route_table = ec2.CfnRouteTable(self, "PrivateSubnet1RouteTable",
                                                         vpc_id=self.vpc.vpc_id)
        Tags.of(private_subnet_1_route_table).add("Name", f"{props['stack_name']}/VPC/PrivateSubnetRouteTable")

        ec2.CfnRoute(self, "PrivateSubnet1DefaultRoute",
                     route_table_id=private_subnet_1_route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     nat_gateway_id=public_subnet_1_nat_gateway.ref)

        """
        Private Subnet 2
        """

        self.private_subnet_2 = ec2.Subnet(self, "PrivateSubnet2",
                                  vpc_id=self.vpc.vpc_id,
                                  availability_zone=self.vpc.availability_zones[1],
                                  cidr_block="10.215.20.0/24",
                                  map_public_ip_on_launch=False)
        Tags.of(self.private_subnet_2).add("Name", f"{props['stack_name']}/VPC/PublicSubnet2")

        private_subnet_2_route_table = ec2.CfnRouteTable(self, "PrivateSubnet2RouteTable",
                                                         vpc_id=self.vpc.vpc_id)
        Tags.of(private_subnet_1_route_table).add("Name", f"{props['stack_name']}/VPC/PrivateSubnet2RouteTable")

        ec2.CfnRoute(self, "PrivateSubnet2DefaultRoute",
                     route_table_id=private_subnet_2_route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     nat_gateway_id=public_subnet_2_nat_gateway.ref)

        # Required for Lambda functions running in VPC to update cloudformation custom resources
        ec2.CfnVPCEndpoint(self, "S3Endpoint",
                           service_name=f"com.amazonaws.{Aws.REGION}.s3",
                           vpc_id=self.vpc.vpc_id,
                           route_table_ids=[private_subnet_1_route_table.ref, private_subnet_2_route_table.ref])
