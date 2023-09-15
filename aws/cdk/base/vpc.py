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
                                   name="PublicSubnets",
                                   subnet_type=ec2.SubnetType.PUBLIC,
                                   cidr_mask=24
                               ),
                               ec2.SubnetConfiguration(
                                   name="PrivateSubnets",
                                   subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                                   cidr_mask=24
                               ),
                           ])
        Tags.of(self.vpc).add("Name", props['stack_name'])

        """
        Public Subnets
        """

        public_subnets = self.vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets
        self.public_subnet_1 = public_subnets[0]
        self.public_subnet_2 = public_subnets[1]

        self.public_route_table = ec2.CfnRouteTable(self, "PublicRouteTable",
                                               vpc_id=self.vpc.vpc_id)
        Tags.of(self.public_route_table).add("Name", f"{props['stack_name']}/VPC/PublicRouteTable")

        ec2.CfnRoute(self, "PublicDefaultRoute",
                     route_table_id=self.public_route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     gateway_id=self.vpc.internet_gateway_id)

        ec2.CfnSubnetRouteTableAssociation(self, "PublicSubnet1RouteTableAssociation",
                                           route_table_id=self.public_route_table.ref,
                                           subnet_id=self.public_subnet_1.subnet_id)

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
        Private Subnets
        """

        private_subnets = self.vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED).subnets
        self.private_subnet_1 = private_subnets[0]
        self.private_subnet_2 = private_subnets[1]

        self.private_subnet_1_route_table = ec2.CfnRouteTable(self, "PrivateSubnet1RouteTable",
                                                         vpc_id=self.vpc.vpc_id)
        Tags.of(self.private_subnet_1_route_table).add("Name", f"{props['stack_name']}/VPC/PrivateSubnetRouteTable")

        ec2.CfnRoute(self, "PrivateSubnet1DefaultRoute",
                     route_table_id=self.private_subnet_1_route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     nat_gateway_id=public_subnet_1_nat_gateway.ref)

        self.private_subnet_2_route_table = ec2.CfnRouteTable(self, "PrivateSubnet2RouteTable",
                                                         vpc_id=self.vpc.vpc_id)
        Tags.of(self.private_subnet_2_route_table).add("Name", f"{props['stack_name']}/VPC/PrivateSubnet2RouteTable")

        ec2.CfnRoute(self, "PrivateSubnet2DefaultRoute",
                     route_table_id=self.private_subnet_2_route_table.ref,
                     destination_cidr_block="0.0.0.0/0",
                     nat_gateway_id=public_subnet_2_nat_gateway.ref)

        # Required for Lambda functions running in VPC to update cloudformation custom resources
        ec2.CfnVPCEndpoint(self, "S3Endpoint",
                           service_name=f"com.amazonaws.{Aws.REGION}.s3",
                           vpc_id=self.vpc.vpc_id,
                           route_table_ids=[self.private_subnet_1_route_table.ref, self.private_subnet_2_route_table.ref])
