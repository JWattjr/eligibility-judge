# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class NegativeControl(gl.Contract):
    """Public test fixture: this contract deliberately provides no GEN payout."""

    def __init__(self):
        pass

    @gl.public.view
    def status(self) -> str:
        return 'Undeployed negative control fixture'

    @gl.public.write
    def claim(self) -> None:
        raise gl.vm.UserError('Native GEN payouts are not implemented in this deliberately negative fixture.')
