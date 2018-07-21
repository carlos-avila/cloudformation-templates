#!/usr/bin/env python3

from troposphere import Ref, Sub, Template, Parameter, rds, ec2

template = Template("""
Template: rds-template.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

vpc = template.add_parameter(Parameter(
    'Vpc',
    Type='AWS::EC2::VPC::Id',
    Description='VPC for the security group',
))

allow_cidr = template.add_parameter(Parameter(
    'AllowCidr',
    Type='String',
    Description='Allows connections to and from the provided CIDR block',
    Default='173.244.44.0/24'
))

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

# region RDS
sec_group = template.add_resource(ec2.SecurityGroup(
    'SecurityGroup',
    GroupDescription=Sub('Default rules'),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            CidrIp=Ref(allow_cidr),
            FromPort=ec2.network_port(5432),
            IpProtocol='tcp',
            ToPort=ec2.network_port(5432),
        )
    ],

    SecurityGroupEgress=[
        ec2.SecurityGroupRule(
            CidrIp=Ref(allow_cidr),
            FromPort=ec2.network_port(5432),
            IpProtocol='tcp',
            ToPort=ec2.network_port(5432),
        )
    ],
    VpcId=Ref(vpc)
))

database = template.add_resource(rds.DBInstance(
    'Database',
    AllocatedStorage=5,
    BackupRetentionPeriod=7,
    DBInstanceClass=Ref(database_instance_class),
    DeletionPolicy='Snapshot',
    Engine=Ref(database_engine),
    MasterUsername=Ref(database_master_username),
    MasterUserPassword=Ref(database_master_password),
    MultiAZ=False,
    PubliclyAccessible=True,
    VPCSecurityGroups=[Ref(sec_group)]
))
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            # Network
            vpc.title: {'default': 'VPC'},
            allow_cidr.title: {'default': 'Allow'},
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
                    vpc.title,
                    allow_cidr.title,
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
