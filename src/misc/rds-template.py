#!/usr/bin/env python3

from troposphere import Ref, Sub, GetAtt
from troposphere import rds, ec2
from troposphere import Template, Parameter, Output

template = Template("""Provides a public, managed database resource with multi-az deployment.

Template: rds-template.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
vpc = template.add_parameter(Parameter(
    'Vpc',
    Type='AWS::EC2::VPC::Id',
    Description='VPC for the security group',
))

allow_cidr = template.add_parameter(Parameter(
    'AllowCidr',
    Type='String',
    Description='Allows connections to and from the provided CIDR block',
    Default='0.0.0.0/0'
))

master_username = template.add_parameter(Parameter(
    'MasterUsername',
    Type='String',
))

master_password = template.add_parameter(Parameter(
    'MasterPassword',
    Type='String',
    NoEcho=True
))

instance_class = template.add_parameter(Parameter(
    'InstanceType',
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

engine = template.add_parameter(Parameter(
    'Engine',
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

storage_type = template.add_parameter(Parameter(
    'StorageType',
    Type='String',
    Description='Specifies the storage type to be associated with the DB instance.',
    Default='standard',
    AllowedValues=['standard', 'gp2', 'io1'],
))
# endregion

# region Resources

sec_group = template.add_resource(ec2.SecurityGroup(
    'SecurityGroup',
    GroupDescription=Sub('${AWS::StackName}'),
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
    AllocatedStorage=10,
    BackupRetentionPeriod=15,
    DBInstanceClass=Ref(instance_class),
    DeletionPolicy='Snapshot',
    Engine=Ref(engine),
    MasterUsername=Ref(master_username),
    MasterUserPassword=Ref(master_password),
    MultiAZ=True,
    StorageEncrypted=False,
    PubliclyAccessible=True,
    VPCSecurityGroups=[Ref(sec_group)]
))
# endregion

# region Output
template.add_output(Output(
    'Address',
    Value=GetAtt(database, 'Endpoint.Address')
))

template.add_output(Output(
    'Port',
    Value=GetAtt(database, 'Endpoint.Port')
))
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            vpc.title: {'default': 'VPC'},
            allow_cidr.title: {'default': 'Allow'},
            engine.title: {'default': 'Engine'},
            instance_class.title: {'default': 'Instance Class'},
            master_username.title: {'default': 'Master Username'},
            master_password.title: {'default': 'Master Password'},

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
                    master_username.title,
                    master_password.title,
                    instance_class.title,
                    engine.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
