from .permissions import adminsOnly
from .misc import *
from .errors import *

# For backward compatibility
sudo_required = adminsOnly("can_restrict_members")
