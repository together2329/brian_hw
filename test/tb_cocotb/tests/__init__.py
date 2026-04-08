"""Test package — imports all submodules so cocotb discovers every @cocotb.test()."""

from tests import test_reset
from tests import test_up_count
from tests import test_down_count
from tests import test_enable
from tests import test_load
from tests import test_direction_switch
from tests import test_stress
from tests import test_param_width