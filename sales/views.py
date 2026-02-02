import csv
from datetime import datetime
from io import BytesIO

from django.db.models import Sum, F, Count, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from .models import Order, OrderItem
from accounts.models import User

from .serializers import (
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)
from inventory.permissions import IsStaffOrManager, IsManager


class OrderFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Order
        fields = ['payment_status', 'start_date', 'end_date']


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = OrderFilter
    search_fields = ['customer__name', 'customer__phone', 'invoice_id']

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsManager()]
        return [IsStaffOrManager()]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderDetailSerializer

    #Generate and download PDF invoice for an order
    @action(detail=True, methods=['get'], url_path='invoice-pdf')
    def generate_invoice(self, request, pk=None):
        order = self.get_object()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Header info
        elements.append(Paragraph(f"Invoice: {order.invoice_id}", styles['Title']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Customer: {order.customer.name}", styles['Normal']))
        elements.append(Paragraph(f"Phone: {order.customer.phone}", styles['Normal']))
        elements.append(Paragraph(f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Paragraph(f"Payment Status: {order.get_payment_status_display()}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Items table
        table_data = [['Product', 'Quantity', 'Unit Price', 'Subtotal']]
        for item in order.items.all():
            table_data.append([
                item.product.name,
                str(item.quantity),
                f"${item.price:.2f}",
                f"${(item.price * item.quantity):.2f}"
            ])
        table_data.append(['', '', 'Total:', f"${order.total_amount:.2f}"])

        table = Table(table_data)
        # table.setStyle(TableStyle([
        #     ('Background', (0, 0), (-1, 0), colors.darkblue),
        #     ('TextColor', (0, 0), (-1, 0), colors.white),
        #     ('Align', (0, 0), (-1, -1), 'CENTER'),
        #     ('FontName', (0, 0), (-1, 0), 'Helvetica-Bold'),
        #     ('FontSize', (0, 0), (-1, 0), 12),
        #     ('BottomPadding', (0, 0), (-1, 0), 12),
        #     ('Background', (0, -1), (-1, -1), colors.beige),
        #     ('FontName', (0, -1), (-1, -1), 'Helvetica-Bold'),
        #     ('Grid', (0, 0), (-1, -1), 1, colors.black),
        # ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{order.invoice_id}.pdf"'
        return response

    @action(detail=False, methods=['get'], url_path='export')
    def export_orders(self, request):
        export_format = request.query_params.get('format', 'csv')
        report_type = request.query_params.get('report', 'total_summary')

        if report_type == 'total_summary':
            headers = ['Date', 'Total Orders', 'Total Sales ($)', 'Total Profit ($)']
            data = self._get_total_summary_data()
        else:  # customer_wise
            headers = ['Customer Name', 'Phone', 'Total Orders', 'Total Spent ($)']
            data = self._get_customer_wise_data()

        if export_format == 'excel':
            return self._export_excel(headers, data, report_type)
        return self._export_csv(headers, data, report_type)

    def _get_total_summary_data(self):
        daily_orders = Order.objects.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_orders=Count('id'),
            total_sales=Sum('total_amount')
        ).order_by('-date')

        data = []
        for row in daily_orders:
            profit = OrderItem.objects.filter(
                order__created_at__date=row['date']
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        (F('price') - F('product__purchase_price')) * F('quantity'),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0

            data.append([
                str(row['date']),
                row['total_orders'],
                f"{row['total_sales']:.2f}",
                f"{profit:.2f}"
            ])
        return data

    # def _get_customer_wise_data(self):
    #     customers = Order.objects.values(
    #         'customer__name', 'customer__phone'
    #     ).annotate(
    #         total_orders=Count('id'),
    #         total_spent=Sum('total_amount')
    #     ).order_by('-total_spent')

    #     data = []
    #     for row in customers:
    #         data.append([
    #             row['customer__name'],
    #             row['customer__phone'],
    #             row['total_orders'],
    #             f"{row['total_spent']:.2f}"
    #         ])
    #     return data

    def _export_csv(self, headers, data, report_type):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(data)
        return response

    # def _export_excel(self, headers, data, report_type):
    #     wb = Workbook()
    #     ws = wb.active
    #     ws.title = report_type.replace('_', ' ').title()

    #     # Header row with styling
    #     ws.append(headers)
    #     header_font = Font(bold=True, color='FFFFFF')
    #     header_fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')
    #     for cell in ws[1]:
    #         cell.font = header_font
    #         cell.fill = header_fill

    #     # Data rows
    #     for row in data:
    #         ws.append(row)

    #     # Auto-width columns
    #     for column in ws.columns:
    #         max_length = max(len(str(cell.value or '')) for cell in column)
    #         ws.column_dimensions[column[0].column_letter].width = max_length + 2

    #     buffer = BytesIO()
    #     wb.save(buffer)
    #     buffer.seek(0)

    #     response = HttpResponse(
    #         buffer.getvalue(),
    #         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     )
    #     response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'
    #     return response


class DashboardView(APIView):
    permission_classes = [IsStaffOrManager]

    def get(self, request):
        today = datetime.now().date()

        total_sales = Order.objects.filter(
            created_at__date=today
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        pending_orders = Order.objects.filter(
            payment_status='unpaid'
        ).count()

        total_paid_orders = Order.objects.filter(created_at__date=today, payment_status='paid').count()

        from inventory.models import Product
        low_stock_products = Product.objects.filter(
            is_active = True,
            quantity__lt=F('min_stock_level')   #When quantity is less than(lt) min stock level
            ).values('id', 'name', 'quantity')
        
        deleted_products = Product.objects.filter(
            is_active = False,
            ).values('id', 'name')

        total_active_users = User.objects.filter(is_active=True).count()
        
        


        data = {
            'paid_orders_today': total_paid_orders,
            'total_sales_today': float(total_sales),
            'pending_orders': pending_orders,
            'total_acitve_users': total_active_users,
            'low_stock_products': low_stock_products,
            'deleted_products': deleted_products,
        }


        # Only managers see profit
        if request.user.role == 'manager':
            total_profit = OrderItem.objects.filter(
                order__created_at__date=today
            ).aggregate(
                profit=Sum(
                    ExpressionWrapper(
                        (F('price') - F('product__purchase_price')) * F('quantity'),
                        output_field=DecimalField()
                    )
                )
            )['profit'] or 0
            data['total_profit_today'] = float(total_profit)

        return Response(data)
