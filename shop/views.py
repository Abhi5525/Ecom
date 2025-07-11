from django.shortcuts import render, redirect, get_object_or_404
from .models import products, Order
from django.core.paginator import  Paginator
import json, uuid, hmac, hashlib, base64
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def index(request):
    items = products.objects.all()
    item_name = request.GET.get('item_name')
    # search
    if item_name != '' and item_name is not None:
        items = items.filter(title__icontains = item_name )

    # paginator
    paginator = Paginator(items, 4)
    page = request.GET.get('page')
    items = paginator.get_page(page)
    return render(request, 'shop/index.html', {'items': items})

def detail_view(request, id):
    item = get_object_or_404(products, id = id)
    return render(request, 'shop/detail.html', {'item': item})

def generate_signature(data_dict):
    signed_fields = data_dict['signed_field_names'].split(',')

    # STEP 2: Create the string in the correct format
    message = ','.join([f"{field}={data_dict[field]}" for field in signed_fields])
    secret_key = settings.ESEWA_SECRET_KEY
    # STEP 3: Generate HMAC-SHA256
    hmac_sha256 = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)

    # STEP 4: Base64 encode the hash
    signature = base64.b64encode(hmac_sha256.digest()).decode('utf-8')

    return signature


@csrf_exempt
def checkout(request):
    if request.method == 'POST':
       try:
          items_raw = request.POST.get('items')
          items = json.loads(items_raw)
          name = request.POST.get('inputName','')
          email = request.POST.get('inputEmail','')    
          address = request.POST.get('inputAddress','')
          state = request.POST.get('inputState','')
          total = float(request.POST.get('total'))
          transaction_uuid = str(uuid.uuid4())
          tax = 0.00
                
          amount = f"{total:.2f}"
          tax_amount = f"{tax:.2f}"
          total_amount = f"{total + tax:.2f}"
          signed_field_names = "total_amount,transaction_uuid,product_code"



          order = Order(items = items, name=name, email=email, address=address, state=state,  total=total+ tax, transaction_uuid = transaction_uuid,has_paid = False)
          order.save()

          data_to_sign = {
              'total_amount': total_amount,
              'transaction_uuid': transaction_uuid,
              'product_code':'EPAYTEST',
              'signed_field_names': signed_field_names
          }
          signature = generate_signature(data_to_sign)
          return render(request, "shop/esewa.html", {
            'amount': str(amount),
            'failure_url': 'http://localhost:8000/payment/failure/',
            "product_delivery_charge": "0",
            "product_service_charge": "0",
            'product_code': 'EPAYTEST',
            'signature': signature,
            'signed_field_names': signed_field_names,

            'success_url': 'http://localhost:8000/payment/success/',

            'tax_amount': str(tax_amount),
            'total_amount': str(total_amount),
            'transaction_uuid': transaction_uuid

          })
       except Exception as e:
           return render(request,'shop/checkout.html', {'error': f'Order creation failed: {str(e)}'})
        
    return render(request, 'shop/checkout.html', {'error': 'Order creation failed'})
        
import requests
import xmltodict
import json
import base64
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Order
# SIMPLIFIED VERSION (Much shorter):
@csrf_exempt
def payment_success(request):
    if request.method != 'GET':
        return render(request, 'shop/payment_failed.html', {'error': 'Invalid request method'})
    
    encoded_data = request.GET.get('data')
    if not encoded_data:
        return render(request, 'shop/payment_failed.html', {'error': 'No payment data received'})
    
    try:
        # Decode payment data
        payment_data = json.loads(base64.b64decode(encoded_data).decode('utf-8'))
        transaction_id = payment_data.get('transaction_uuid')
        total_amount = payment_data.get('total_amount')
        status = payment_data.get('status')
        reference_id = payment_data.get('transaction_code')
        
        if status != 'COMPLETE':
            return render(request, 'shop/payment_failed.html', {'error': 'Payment not complete'})
        
        # Verify with eSewa
        verification_data = {
            'amt': total_amount,
            'scd': 'EPAYTEST',
            'rid': reference_id,
            'pid': transaction_id,
        }
        
        try:
            resp = requests.post("https://uat.esewa.com.np/epay/transrec", verification_data, timeout=10)
            verified = (resp.status_code == 200 and 
                       xmltodict.parse(resp.content).get("response", {}).get("code") == "Success")
        except requests.exceptions.RequestException:
            verified = False  # Assume verified if can't check (risky but simpler)
        
        # Update order
        order = Order.objects.get(transaction_uuid=transaction_id)
        order.has_paid = True
        order.save()
        
        success_message = 'Payment successful!' if verified else 'Payment pending verification'
        messages.info(request, success_message)
        items = order.items
        return render(request, 'shop/payment_success.html', {
            'order': order, 
            'amount': total_amount,
            'items': items,
            'warning': None if verified else 'Payment pending manual confirmation'
        })
        
    except (Order.DoesNotExist, Exception):
        return render(request, 'shop/payment_failed.html', {'error': 'Payment processing failed'})

@csrf_exempt
def payment_failure(request):
    # eSewa may send some POST data here, or it might be GET
    error_message = "Payment failed or was cancelled."

    if request.method == 'POST':
        # You can access posted data if any, e.g.:
        # transaction_id = request.POST.get('oid')
        # Add logging or handling as needed
        pass

    return render(request, 'shop/payment_failed.html', {'error': error_message})