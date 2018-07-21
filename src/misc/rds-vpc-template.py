#!/usr/bin/env python3

from troposphere import Ref, Sub, GetAtt, Tags
from troposphere import Template, Parameter, ec2, rds

template = Template("""
Create a RDS instance in a VPC.

Template: rds-vpc-template
Author: Carlos Avila <cavila@mandelbrew.com>
""")

# region Parameters - Network
allow_acess_cidr = template.add_parameter(Parameter(
    'AllowAccessCidr',
    Type='String',
    Description='Allows all connections to and from the provided CIDR block',
    Default='173.244.44.0/24'
))

vpc_cidr_block = template.add_parameter(Parameter(
    'VpcCidrBlock',
    Type='String',
    Description='Specifies the CIDR Block of VPC',
    Default='10.0.0.0/16'
))

subnet1_cidr_block = template.add_parameter(Parameter(
    'Subnet1CidrBlock',
    Type='String',
    Description='Specifies the CIDR Block of Subnet 1',
    Default='10.0.0.0/24'
))

subnet2_cidr_block = template.add_parameter(Parameter(
    'Subnet2CidrBlock',
    Type='String',
    Description='Specifies the CIDR Block of Subnet 2',
    Default='10.0.1.0/24'
))
# endregion

# region Parameters - Database
database_master_username = template.add_parameter(Parameter(
    'DatabaseMasterUsername',
    Type='String',
))

database_master_password = template.add_parameter(Parameter(
    'DatabaseMasterPassword',
    Type='String',
    NoEcho=True
))

database_instance_class = template.add_parameter(Parameter(
    'DatabaseInstanceType',
    Type='String',
    Default='db.t2.micro',
    AllowedValues=[
        'db.t1.micro',
        'db.t2.micro', 'db.t2.small', 'db.t2.medium', 'db.t2.large',
        'db.m1.small', 'db.m1.medium', 'db.m1.large', 'db.m1.xlarge',
        'db.m2.xlarge', 'db.m2.2xlarge', 'db.m2.4xlarge',
        'db.m3.medium', 'db.m3.large', 'db.m3.xlarge', 'db.m3.2xlarge',
        'db.m4.large', 'db.m4.xlarge', 'db.m4.2xlarge', 'db.m4.4xlarge', 'db.m4.10xlarge',
        'db.r3.large', 'db.r3.xlarge', 'db.r3.2xlarge', 'db.r3.4xlarge', 'db.r3.8xlarge',
    ]
))

database_engine = template.add_parameter(Parameter(
    'DatabaseEngine',
    Type='String',
    Description='The name of the database engine to be used',
    Default='postgres',
    AllowedValues=['aurora',
                   'mariadb',
                   'mysql',
                   'oracle-ee',
                   'oracle-se2',
                   'oracle-se1',
                   'oracle-se',
                   'postgres',
                   'sqlserver-ee',
                   'sqlserver-se',
                   'sqlserver-ex',
                   'sqlserver-web', ]
))
# endregion

# region Network
vpc = template.add_resource(ec2.VPC(
    'Vpc',
    CidrBlock=Ref(vpc_cidr_block),
    EnableDnsSupport=True,
    EnableDnsHostnames=True,
    Tags=Tags(StackName=Sub('${AWS::StackName}'))
))
subnet1 = template.add_resource(ec2.Subnet(
    'Subnet1',
    VpcId=Ref(vpc),
    AvailabilityZone=Sub('${AWS::Region}a'),
    CidrBlock=Ref(subnet1_cidr_block),
    MapPublicIpOnLaunch=True,
    Tags=Tags(StackName=Sub('${AWS::StackName}'))
))
subnet2 = template.add_resource(ec2.Subnet(
    'Subnet2',
    VpcId=Ref(vpc),
    AvailabilityZone=Sub('${AWS::Region}b'),
    CidrBlock=Ref(subnet2_cidr_block),
    MapPublicIpOnLaunch=True,
    Tags=Tags(StackName=Sub('${AWS::StackName}'))
))
# Gateway used by the VPC to connect to the internet
internet_gateway = template.add_resource(ec2.InternetGateway(
    'InternetGateway',
    Tags=Tags(StackName=Sub('${AWS::StackName}'))
))
# Map our VPC to our gateway
gateway_attachment = template.add_resource(ec2.VPCGatewayAttachment(
    'GatewayAttachment',
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(internet_gateway),
))
# Routing table used by our VPC
route_table = template.add_resource(ec2.RouteTable(
    'RouteTable',
    VpcId=Ref(vpc),
    Tags=Tags(StackName=Sub('${AWS::StackName}'))
))
# Routing rule that gets added to our routing table for our internet gateway
route = template.add_resource(ec2.Route(
    'Route',
    DependsOn=[gateway_attachment.title],
    RouteTableId=Ref(route_table),
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=Ref(internet_gateway)
))
# Associate all subnets with our routing table too
subnet1_route_table_association = template.add_resource(ec2.SubnetRouteTableAssociation(
    'Subnet1RouteTableAssociation',
    SubnetId=Ref(subnet1),
    RouteTableId=Ref(route_table)
))
subnet2_route_table_association = template.add_resource(ec2.SubnetRouteTableAssociation(
    'Subnet2RouteTableAssociation',
    SubnetId=Ref(subnet2),
    RouteTableId=Ref(route_table)
))

backdoor_sgi = template.add_resource(ec2.SecurityGroupIngress(
    'BackdoorSecurityGroupIngress',
    CidrIp=Ref(allow_acess_cidr),
    FromPort=ec2.network_port(-1),
    GroupId=GetAtt(vpc, 'DefaultSecurityGroup'),
    IpProtocol='-1',
    ToPort=ec2.network_port(-1),
))
# endregion

# region RDS
database_sg = template.add_resource(rds.DBSubnetGroup(
    'DatabaseSubnetGroup',
    DBSubnetGroupDescription=Sub('Subnets available for ${AWS::StackName}'),
    SubnetIds=[
        Ref(subnet1),
        Ref(subnet2)
    ]
))

database = template.add_resource(rds.DBInstance(
    'Database',
    DependsOn=[gateway_attachment.title],  # PubliclyAccessible requires gateway attachment
    AllocatedStorage=5,
    BackupRetentionPeriod=7,
    DBInstanceClass=Ref(database_instance_class),
    DeletionPolicy='Snapshot',
    Engine=Ref(database_engine),
    MasterUsername=Ref(database_master_username),
    MasterUserPassword=Ref(database_master_password),
    MultiAZ=False,
    PubliclyAccessible=True,
    DBSubnetGroupName=Ref(database_sg),
    VPCSecurityGroups=[
        GetAtt(vpc, 'DefaultSecurityGroup')
    ]
))
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            # Network
            allow_acess_cidr.title: {'default': 'Allow'},
            vpc_cidr_block.title: {'default': 'VPC'},
            subnet1_cidr_block.title: {'default': 'Subnet 1'},
            subnet2_cidr_block.title: {'default': 'Subnet 2'},
            # Database Service
            database_engine.title: {'default': 'Engine'},
            database_instance_class.title: {'default': 'Instance Class'},
            database_master_username.title: {'default': 'Master Username'},
            database_master_password.title: {'default': 'Master Password'},

        },
        'ParameterGroups': [
            {
                'Label': {'default': 'Network'},
                'Parameters': [
                    allow_acess_cidr.title,
                    vpc_cidr_block.title,
                    subnet1_cidr_block.title,
                    subnet2_cidr_block.title,
                ]
            },
            {
                'Label': {'default': 'Database Service'},
                'Parameters': [
                    database_master_username.title,
                    database_master_password.title,
                    database_instance_class.title,
                    database_engine.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
