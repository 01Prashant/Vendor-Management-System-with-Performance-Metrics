from rest_framework import status
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import VendorSerializer, PurchaseOrderSerializer, HistoricalPerformanceSerializer

# Create your views here.

# Vendors API
@api_view(['GET', 'POST'])
def vendor_list(request):
    if request.method == 'GET':
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            vendor = serializer.instance

            historical_data = HistoricalPerformance.objects.create(
                vendor=vendor,
                date=timezone.now(),
                on_time_delivery_rate=request.data.get('on_time_delivery_rate', 0),
                quality_rating_avg=request.data.get('quality_rating_avg', 0),
                average_response_time=request.data.get('average_response_time', 0),
                fulfillment_rate=request.data.get('fulfillment_rate', 0)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def vendor_detail(request, vendor_code):
    try:
        vendor = Vendor.objects.get(vendor_code=vendor_code)
    except Vendor.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = VendorSerializer(vendor, data=request.data)
        if serializer.is_valid():
            old_vendor_data = Vendor.objects.filter(vendor_code=vendor_code).values('on_time_delivery_rate', 'quality_rating_avg', 'average_response_time', 'fulfillment_rate').first()
            serializer.save()
            new_vendor_data = request.data

            if (old_vendor_data['on_time_delivery_rate'] != new_vendor_data.get('on_time_delivery_rate') or
                old_vendor_data['quality_rating_avg'] != new_vendor_data.get('quality_rating_avg') or
                old_vendor_data['average_response_time'] != new_vendor_data.get('average_response_time') or
                old_vendor_data['fulfillment_rate'] != new_vendor_data.get('fulfillment_rate')):
                
                historical_data = HistoricalPerformance.objects.create(
                    vendor=vendor,
                    date=timezone.now(),
                    on_time_delivery_rate=new_vendor_data.get('on_time_delivery_rate', 0),
                    quality_rating_avg=new_vendor_data.get('quality_rating_avg', 0),
                    average_response_time=new_vendor_data.get('average_response_time', 0),
                    fulfillment_rate=new_vendor_data.get('fulfillment_rate', 0)
                )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        vendor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# Purchase Order API
@api_view(['GET', 'POST'])
def purchase_order_list(request):
    if request.method == 'GET':
        purchase_orders = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            purchase_order = serializer.instance

            vendor = purchase_order.vendor
            
            # Calculate On-Time Delivery Rate
            completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
            on_time_deliveries = completed_pos.filter(delivery_date__lte=purchase_order.delivery_date).count()
            vendor.on_time_delivery_rate = (on_time_deliveries / completed_pos.count()) * 100 if completed_pos.count() else 0
            
            # Calculate Quality Rating Average
            quality_ratings = PurchaseOrder.objects.filter(vendor=vendor, quality_rating__isnull=False).values_list('quality_rating', flat=True)
            vendor.quality_rating_avg = sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0
            
            # Calculate Average Response Time
            ack_times = PurchaseOrder.objects.filter(vendor=vendor, acknowledgment_date__isnull=False).values_list('acknowledgment_date', 'issue_date')
            avg_response_time = sum((ack - issue).total_seconds() for ack, issue in ack_times) / len(ack_times) if ack_times else 0
            vendor.average_response_time = avg_response_time / 3600
            
            # Calculate Fulfillment Rate
            fulfilled_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed').exclude(quality_rating__isnull=True)
            vendor.fulfillment_rate = (fulfilled_pos.count() / PurchaseOrder.objects.filter(vendor=vendor).count()) * 100 if PurchaseOrder.objects.filter(vendor=vendor).count() else 0
            
            vendor.save()
            HistoricalPerformance.objects.create(
                vendor=vendor,
                date=timezone.now(),
                on_time_delivery_rate=vendor.on_time_delivery_rate,
                quality_rating_avg=vendor.quality_rating_avg,
                average_response_time=vendor.average_response_time,
                fulfillment_rate=vendor.fulfillment_rate
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def purchase_order_detail(request, po_number):
    try:
        purchase_order = PurchaseOrder.objects.get(po_number=po_number)
    except PurchaseOrder.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PurchaseOrderSerializer(purchase_order)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PurchaseOrderSerializer(purchase_order, data=request.data)
        if serializer.is_valid():
            original_purchase_order_data = PurchaseOrder.objects.get(pk=purchase_order.pk)
            serializer.save()
            updated_purchase_order = serializer.instance
            
            relevant_fields_changed = (
                updated_purchase_order.delivery_date != original_purchase_order_data.delivery_date or
                updated_purchase_order.quality_rating != original_purchase_order_data.quality_rating or
                updated_purchase_order.acknowledgment_date != original_purchase_order_data.acknowledgment_date or
                updated_purchase_order.status != original_purchase_order_data.status
            )
            
            if relevant_fields_changed:
                vendor = updated_purchase_order.vendor
                
                # Calculate On-Time Delivery Rate
                completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
                on_time_deliveries = completed_pos.filter(delivery_date__lte=updated_purchase_order.delivery_date).count()
                vendor.on_time_delivery_rate = (on_time_deliveries / completed_pos.count()) * 100 if completed_pos.count() else 0
                
                # Calculate Quality Rating Average
                quality_ratings = PurchaseOrder.objects.filter(vendor=vendor, quality_rating__isnull=False).values_list('quality_rating', flat=True)
                vendor.quality_rating_avg = sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0
                
                # Calculate Average Response Time
                ack_times = PurchaseOrder.objects.filter(vendor=vendor, acknowledgment_date__isnull=False).values_list('acknowledgment_date', 'issue_date')
                avg_response_time = sum((ack - issue).total_seconds() for ack, issue in ack_times) / len(ack_times) if ack_times else 0
                vendor.average_response_time = avg_response_time / 3600  # Convert seconds to hours
                
                # Calculate Fulfillment Rate
                fulfilled_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed').exclude(quality_rating__isnull=True)
                vendor.fulfillment_rate = (fulfilled_pos.count() / PurchaseOrder.objects.filter(vendor=vendor).count()) * 100 if PurchaseOrder.objects.filter(vendor=vendor).count() else 0
                
                vendor.save()
                HistoricalPerformance.objects.create(
                    vendor=vendor,
                    date=timezone.now(),
                    on_time_delivery_rate=vendor.on_time_delivery_rate,
                    quality_rating_avg=vendor.quality_rating_avg,
                    average_response_time=vendor.average_response_time,
                    fulfillment_rate=vendor.fulfillment_rate
                )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        purchase_order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# Vendor Performance API
@api_view(['GET'])
def vendor_performance_detail(request, vendor_id):
    latest_performance_data = HistoricalPerformance.objects.filter(vendor_id=vendor_id).order_by('-date').first()
    
    if not latest_performance_data:
        return Response({"error": "Performance data not found for the vendor"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = HistoricalPerformanceSerializer(latest_performance_data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def acknowledge_purchase_order(request, po_id):
    try:
        purchase_order = PurchaseOrder.objects.get(id=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'POST':
        acknowledgment_date = request.data.get('acknowledgment_date')
        
        purchase_order.acknowledgment_date = acknowledgment_date
        purchase_order.save()
        
        # Calculate the average response time for the vendor
        vendor = purchase_order.vendor
        ack_times = PurchaseOrder.objects.filter(vendor=vendor, acknowledgment_date__isnull=False).values_list('acknowledgment_date', 'issue_date')
        avg_response_time = sum((ack - issue).total_seconds() for ack, issue in ack_times) / len(ack_times) if ack_times else 0
        vendor.average_response_time = avg_response_time / 3600
        vendor.save()
        
        HistoricalPerformance.objects.create(
            vendor=vendor,
            date=timezone.now(),
            on_time_delivery_rate=vendor.on_time_delivery_rate,
            quality_rating_avg=vendor.quality_rating_avg,
            average_response_time=vendor.average_response_time,
            fulfillment_rate=vendor.fulfillment_rate
        )
        return Response({"message": "Purchase order acknowledged successfully."}, status=status.HTTP_200_OK)
    return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)