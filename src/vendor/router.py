from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from websockets.exceptions import ConnectionClosedError

from src.websocket_manager import WebsocketManager

from src.auth.jwt_bearer import SupabaseJWTBearer
from src.vendor.dependencies import (
    get_vendor_by_name,
    get_vendor_by_name_ws,
    get_vendor_menu,
    vendor_exists,
    parse_new_vendor_details,
    food_linked_to_vendor,
    food_linked_to_vendor_name,
)
from src.vendor.models import (
    Vendor,
    VendorCreate,
    VendorOut,
    Food,
    FoodCreate,
    FoodOut,
    FoodUpdate,
    STATUS,
)
from src.vendor.service import (
    create_vendor,
    update_vendor_status,
    insert_food,
    update_food,
    delete_food,
    get_next_order_from_queue,
)
from src.vendor.schema import HTTPError, StatusUpdateOut

from src.order.models import OrderOut


router = APIRouter(
    prefix="/vendor",
    tags=["vendor"],
    dependencies=[Depends(SupabaseJWTBearer)],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=VendorOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exist",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def get_current_signed_vendor(
    vendor: Vendor = Depends(vendor_exists),
) -> VendorOut:
    return vendor


@router.get(
    "/{vendor_name}",
    status_code=status.HTTP_200_OK,
    response_model=VendorOut,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPError,
            "description": "Vendor not found",
        }
    },
)
async def get_vendor_with_name(
    vendor: Vendor = Depends(get_vendor_by_name),
) -> VendorOut:
    return vendor


@router.post(
    "/new",
    status_code=status.HTTP_201_CREATED,
    response_model=VendorOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor already exists",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def new_vendor(
    vendor_details: VendorCreate = Depends(parse_new_vendor_details),
) -> VendorOut:

    vendor = await create_vendor(vendor_details=vendor_details)

    return vendor


@router.patch(
    "/change-status",
    status_code=status.HTTP_200_OK,
    response_model=StatusUpdateOut | HTTPError,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": HTTPError,
            "description": "Unable to update status",
        },
    },
)
async def change_status(
    new_status: STATUS, vendor: Vendor = Depends(vendor_exists)
) -> StatusUpdateOut | HTTPError:
    """Switch vendor status from open to closed or vice versa"""

    i = await update_vendor_status(new_status=new_status, vendor=vendor)

    if i == 0:
        return {"detail": "status updated", "status": vendor.status}
    else:
        raise HTTPException(status_code=500, detail="Unable to update status")


@router.get(
    "/{vendor_name}/menu",
    status_code=status.HTTP_200_OK,
    response_model=list[FoodOut],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPError,
            "description": "Vendor not found",
        }
    },
)
async def get_menu(menu=Depends(get_vendor_menu)) -> list[FoodOut]:
    """Gets the list of the foods that a vendor provides"""

    return menu


@router.get(
    "/{vendor_name}/menu/{food_name}",
    status_code=status.HTTP_200_OK,
    response_model=FoodOut,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPError,
            "description": "Vendor not found",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPError,
            "description": "Food not found",
        },
    },
)
async def get_food(
    food: Food = Depends(food_linked_to_vendor_name),
) -> FoodOut:
    """Gets certain food from a given vendor"""

    return food


@router.post(
    "/menu",
    status_code=status.HTTP_201_CREATED,
    response_model=list[FoodOut],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exists",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def add_food_to_menu(
    food_create: FoodCreate | list[FoodCreate],
    vendor: Vendor = Depends(vendor_exists),
) -> list[FoodOut]:
    """Add food to the vendor's menu"""

    new_food = await insert_food(food_create, vendor)

    return new_food


@router.patch(
    "/menu",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=FoodOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exists",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Updating invalid food",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def update_food_in_menu(
    food_update: FoodUpdate,
    old_food: Food = Depends(food_linked_to_vendor),
) -> FoodOut:
    """Update food in the vendor's menu"""

    new_food = await update_food(food_update, old_food)

    return new_food


@router.delete(
    "/menu",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exists",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Deleting invalid food",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def delete_food_from_menu(
    food: Food = Depends(food_linked_to_vendor),
    vendor: Vendor = Depends(vendor_exists),
):
    """Delete food from the vendor's menu"""

    await delete_food(food, vendor)

    return {"detail": "OK"}


@router.get(
    "/orders/all",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderOut],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exists",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def get_all_orders(
    vendor: Vendor = Depends(vendor_exists),
) -> list[OrderOut]:
    """Gets a list of all the orders a vendor has.

    Waiting, processing and completed orders are returned.
    """

    await vendor.fetch_link("orders")

    return vendor.orders


@router.get(
    "/orders/next",
    status_code=status.HTTP_200_OK,
    response_model=OrderOut | None,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Vendor does not exists",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPError,
            "description": "Forbidden",
        },
    },
)
async def get_next_order(
    vendor: Vendor = Depends(vendor_exists),
) -> OrderOut | None:
    """Gets the next order from the vendor's queue"""

    next_order = await get_next_order_from_queue(vendor=vendor)

    return next_order


@router.websocket("/{vendor_name}/ws/order-count")
async def current_orders(
    websocket: WebSocket,
    vendor: Vendor = Depends(get_vendor_by_name_ws),
):
    """Gets number of orders that a vendor currently has waiting"""

    name = vendor.name

    websocket_manager = WebsocketManager()

    await websocket_manager.connect(name, websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect as e:
        if not (e.code == status.WS_1010_MANDATORY_EXT):
            # If the disconnect was not raised by the websocket_manager
            websocket_manager.remove_connection(name)

    except ConnectionClosedError:
        websocket_manager.remove_connection(name)
