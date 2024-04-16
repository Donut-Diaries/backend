from fastapi import APIRouter, Depends, HTTPException, status


from src.order.dependencies import validate_order_create
from src.order.models import OrderOut
from src.order.schema import OrderVendorConsumer, HTTPError
from src.order.service import create_order

router = APIRouter(prefix="/order", tags=["order"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exists",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Consumer does not exist",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def place_order(
    order: OrderVendorConsumer = Depends(validate_order_create),
) -> OrderOut:
    """Make a new order"""

    try:
        created_order = await create_order(order)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Unable to order currently"
        )

    return created_order
