"""Package entry point; plan mode reads metadata only."""
import json

from . import native_bulk_controller as controller


if __name__ == '__main__':
    try:
        print(json.dumps(controller.main()))
    except Exception as error:
        print(json.dumps({'status': 'held', 'error_class': getattr(error, 'code',
                         str(error) if isinstance(error, controller.contract.ContractError)
                         else 'bulk_controller_failed')}))
        raise SystemExit(3)
