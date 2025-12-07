import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..db import crud
from ..dependencies import DBSessionDependency, UserDependency
from ..schemas.forecast import ForecastResponse
from ..services.forecast import forecast


logger = logging.getLogger(__name__)
router = APIRouter(tags=["forecast"])


@router.get("/api/forecast/", response_model=ForecastResponse)
def get_forecast(
    db: DBSessionDependency,
    user: UserDependency,
    goods_id: UUID | None = None,
    day_forecast: int = 7,
):
    """
    Get forecast data for goods with lowest stock.

    Returns top 10 goods with lowest stock quantity along with their sales history
    grouped by date. This dataset is prepared for forecast model training/prediction.

    Query Parameters:
        goods_id (optional): If provided, return forecast data only for this specific goods
        day_forecast (optional): Number of days to forecast ahead (default: 7)

    Response:
        List of goods with the following structure:
        {
            "id": UUID,
            "name": str,
            "category": str (optional),
            "price": float,
            "stock_quantity": int,
            "created_at": datetime,
            "sales_dataset": [
                {
                    "date": str (YYYY-MM-DD),
                    "total_quantity": int,
                }
            ],
            "is_forecasted": bool,
            "forecast": [
                {
                    "date": str (YYYY-MM-DD),
                    "total_sales": int,
                    "max_sales": int,
                    "min_sales": int
                }
            ]
        }
    """
    try:
        if not goods_id:
            # Get top 10 goods with lowest stock
            low_stock_goods = crud.get_top_low_stock_goods(
                db=db, user_id=user.id, limit=10
            )

            # Prepare response with sales dataset for each goods
            forecast_data = []
            for goods in low_stock_goods:
                # Get sales dataset grouped by date
                sales_dataset = crud.get_sales_dataset_by_goods(
                    db=db, goods_id=goods.id, user_id=user.id
                )

                goods_data = {
                    "id": goods.id,
                    "name": goods.name,
                    "category": goods.category,
                    "price": goods.price,
                    "stock_quantity": goods.stock_quantity,
                    "created_at": goods.created_at,
                    "sales": sales_dataset,
                }

                if len(sales_dataset) > 7:
                    goods_data["is_forecasted"] = True
                    # Check if forecast already exists for today
                    existing_inference = crud.get_restock_inference_by_goods_and_date(
                        db=db, goods_id=goods.id, user_id=user.id
                    )

                    if existing_inference and existing_inference.future_preds:
                        # Use existing forecast from DB
                        goods_data["forecast"] = existing_inference.future_preds
                    else:
                        # Generate new forecast and save to DB
                        forecast_result = forecast(
                            sales_dataset, day_forecast=day_forecast
                        )
                        goods_data["forecast"] = forecast_result

                        # Save to database
                        try:
                            crud.create_restock_inference(
                                db=db,
                                goods_id=goods.id,
                                total_quantity=forecast_result.get(
                                    "restock_quantity", 0
                                ),
                                future_preds=forecast_result,
                            )
                        except Exception as e:
                            logger.warning(f"Failed to save forecast to DB: {str(e)}")
                else:
                    goods_data["is_forecasted"] = False

                forecast_data.append(goods_data)
        else:
            goods = crud.get_goods_by_id(db, goods_id, user.id)
            sales_dataset = crud.get_sales_dataset_by_goods(db, goods.id, user.id)
            forecast_data = {
                "id": goods.id,
                "name": goods.name,
                "category": goods.category,
                "price": goods.price,
                "stock_quantity": goods.stock_quantity,
                "created_at": goods.created_at,
                "sales": sales_dataset,
            }

            if len(sales_dataset) > 7:
                forecast_data["is_forecasted"] = True
                # Check if forecast already exists for today
                existing_inference = crud.get_restock_inference_by_goods_and_date(
                    db=db, goods_id=goods.id, user_id=user.id
                )

                if existing_inference and existing_inference.future_preds:
                    # Use existing forecast from DB
                    forecast_data["forecast"] = existing_inference.future_preds
                else:
                    # Generate new forecast and save to DB
                    forecast_result = forecast(sales_dataset, day_forecast=day_forecast)
                    forecast_data["forecast"] = forecast_result

                    # Save to database
                    try:
                        crud.create_restock_inference(
                            db=db,
                            goods_id=goods.id,
                            total_quantity=forecast_result.get("restock_quantity", 0),
                            future_preds=forecast_result,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save forecast to DB: {str(e)}")
            else:
                forecast_data["is_forecasted"] = False
            forecast_data = [forecast_data]

        return {"data": forecast_data}

    except Exception as e:
        logger.error(f"Error in forecast endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating forecast data")
