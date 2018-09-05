from troposphere import Ref
from troposphere import Equals

import parameters

has_slim_handler = 'HasSlimHandler'

conditions = {
    has_slim_handler: Equals(Ref(parameters.slim_handler), 'True')
}
