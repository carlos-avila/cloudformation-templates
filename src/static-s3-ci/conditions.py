from troposphere import Ref
from troposphere import Equals, Not, Condition

import parameters

UseSourceS3 = 'UseSourceS3'
UseSourceRepo = ' UseSourceRepo'
RequireApproval = 'RequireApproval'

conditions = {
    UseSourceS3: Equals(Ref(parameters.source_provider), 'S3'),
    UseSourceRepo: Not(Condition(UseSourceS3)),
    RequireApproval: Equals(Ref(parameters.require_approval), 'True')
}
