from rest_framework.views import APIView
from .models import GasStock, Sale
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .serializers import GasStockSerializer, SaleSerializer
from user_management.apps.base.utils.permissions import IsStaffOrSuperUser, IsAdmin
from datetime import datetime
from user_management.apps.base.utils.response_structure import api_response  # Assuming `api_response` is in a `utils.py` file


class MakeSaleView(APIView):
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="make_sale",
        summary="Record a Sale",
        description="Allows staff and admin users to record sales by specifying the kilograms sold. Adjusts the stock accordingly.",
        request={
            "kg_sold": "float - The kilograms sold in this transaction."
        },
        responses={
            200: OpenApiResponse(
                response=SaleSerializer,
                description="Sale recorded successfully.",
                examples=[
                    OpenApiExample(
                        "Successful Sale",
                        value={
                            "response_status": "success",
                            "response_description": "Sale recorded successfully.",
                            "response_data": {
                                "id": "01AKFHCNS33HDKS",
                                "kg_sold": 5.0,
                                "total_price": 500.0,
                                "created_at": "2025-05-02T12:00:00Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=SaleSerializer,
                description="Validation error or insufficient stock.",
                examples=[
                    OpenApiExample(
                        "Error: Insufficient Stock",
                        value={
                            "response_status": "failure",
                            "response_description": "Not enough stock available.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        try:
            data = request.data
            kg_sold = data.get('kg_sold')
            if not kg_sold:
                return api_response("error", "Kg sold field is required.")

            gas_stock = GasStock.get_instance()
            if kg_sold > gas_stock.total_kg:
                return api_response("error", "Not enough stock available.")

            sale = Sale.objects.create(
                kg_sold=kg_sold,
                created_by=request.user,
                updated_by=request.user,
            )
            gas_stock.sell_stock(kg_sold)
            return api_response("success", "Sale recorded successfully.", SaleSerializer(sale).data)
        except Exception as e:
            return api_response("error", "An error occurred while recording the sale.", {"details": str(e)})


class AddStockView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        operation_id="add_stock",
        summary="Add Stock",
        description="Allows admin users to add stock in kilograms to the system. Adjusts the total stock accordingly.",
        request={
            "kilograms": "float - The kilograms to be added to the stock."
        },
        responses={
            200: OpenApiResponse(
                response=GasStockSerializer,
                description="Stock added successfully.",
                examples=[
                    OpenApiExample(
                        "Stock Added",
                        value={
                            "response_status": "success",
                            "response_description": "Stock added successfully.",
                            "response_data": {
                                "total_kg": 149.0
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=GasStockSerializer,
                description="Validation error or unexpected error.",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Kilograms field is required.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        try:
            data = request.data
            kilograms = data.get('kilograms')
            if not kilograms:
                return api_response("error", "Kilograms field is required.")
            
            gas_stock = GasStock.get_instance()
            gas_stock.add_stock(kilograms)
            return api_response("success", "Stock added successfully.", {"total_kg": gas_stock.total_kg})
        except Exception as e:
            return api_response("error", "An error occurred while adding stock.", {"details": str(e)})


class ViewSalesView(APIView):
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="view_sales",
        summary="View Sales for a Specific Day",
        description="Retrieves a list of sales filtered by a specific date, provided in the query parameter.",
        parameters=[
            {
                "name": "date",
                "in": "query",
                "description": "Date in 'YYYY-MM-DD' format.",
                "required": True,
                "type": "string"
            }
        ],
        responses={
            200: OpenApiResponse(
                response=SaleSerializer,
                description="Sales retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Sales List",
                        value={
                            "response_status": "success",
                            "response_description": "Sales retrieved successfully.",
                            "response_data": [
                                {
                                    "id": "01AKFHCNS33HDKS",
                                    "kg_sold": 5.0,
                                    "total_price": 500.0,
                                    "created_at": "2025-05-02T12:00:00Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=SaleSerializer,
                description="Invalid date or other validation error.",
                examples=[
                    OpenApiExample(
                        "Invalid Date Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Date query parameter is required.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        try:
            date_str = request.query_params.get('date')
            if not date_str:
                return api_response("error", "Date query parameter is required.")

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            sales = Sale.objects.filter(created_at__date=date)
            serializer = SaleSerializer(sales, many=True)
            return api_response("success", "Sales retrieved successfully.", serializer.data)
        except Exception as e:
            return api_response("error", "An error occurred while retrieving sales.", {"details": str(e)})


class SalesSummaryView(APIView):
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="sales_summary",
        summary="Retrieve Sales Summary for a Specific Day",
        description="Provides a summary of total kilograms sold and total revenue for a given day.",
        parameters=[
            {
                "name": "date",
                "in": "query",
                "description": "Date in 'YYYY-MM-DD' format.",
                "required": True,
                "type": "string"
            }
        ],
        responses={
            200: OpenApiResponse(
                response=SaleSerializer,
                description="Sales summary retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Sales Summary",
                        value={
                            "response_status": "success",
                            "response_description": "Sales summary retrieved successfully.",
                            "response_data": {
                                "total_kg_sold": 50.0,
                                "total_amount": 5000.0
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=SaleSerializer,
                description="Invalid date or other error.",
                examples=[
                    OpenApiExample(
                        "Invalid Date Error",
                        value={
                            "response_status": "failure",
                            "response_description": "Date query parameter is required.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        try:
            date_str = request.query_params.get('date')
            if not date_str:
                return api_response("error", "Date query parameter is required.")

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            sales = Sale.objects.filter(created_at__date=date)

            total_kg = sum(sale.kg_sold for sale in sales)
            total_amount = sum(sale.total_price for sale in sales)

            summary = {
                "total_kg_sold": total_kg,
                "total_amount": total_amount,
            }
            return api_response("success", "Sales summary retrieved successfully.", summary)
        except Exception as e:
            return api_response("error", "An error occurred while retrieving the summary.", {"details": str(e)})


class ViewStockView(APIView):
    permission_classes = [IsStaffOrSuperUser]

    @extend_schema(
        operation_id="view_stock",
        summary="View Current Stock Details",
        description="Retrieves the current stock details, including the number of full cylinders and the remaining kilograms in the current cylinder.",
        responses={
            200: OpenApiResponse(
                response=GasStockSerializer,
                description="Stock details retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Stock Details",
                        value={
                            "response_status": "success",
                            "response_description": "Stock details retrieved successfully.",
                            "response_data": {
                                "total_cylinders": 10,
                                "remaining_kg_in_current_cylinder": 5.0
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=GasStockSerializer,
                description="Unexpected error.",
                examples=[
                    OpenApiExample(
                        "Unexpected Error",
                        value={
                            "response_status": "failure",
                            "response_description": "An error occurred while retrieving stock details.",
                            "response_data": {}
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        try:
            gas_stock = GasStock.get_instance()
            total_kg = gas_stock.total_kg

            cylinders = int(total_kg // 49)  # Full cylinders
            remainder = total_kg % 49  # Remaining kg in current cylinder

            stock_info = {
                "total_cylinders": cylinders,
                "remaining_kg_in_current_cylinder": remainder,
            }
            return api_response("success", "Stock details retrieved successfully.", stock_info)
        except Exception as e:
            return api_response("error", "An error occurred while retrieving stock details.", {"details": str(e)})
