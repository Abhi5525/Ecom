
# from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import SignUpForm, LoginForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import products, Order
from django.core.paginator import  Paginator
import json, uuid, hmac, hashlib, base64
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order, User

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
@login_required
@csrf_exempt
def checkout(request):
    print("=" * 50)
    print("CHECKOUT VIEW DEBUG")
    print("=" * 50)
    print(f"Request method: {request.method}")
    print(f"User: {request.user}")
    print(f"User ID: {request.user.id}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    
    if request.method == 'POST':
        print("\n--- POST REQUEST DATA ---")
        print(f"All POST data: {dict(request.POST)}")
        
        try:
            # Debug each field
            items_raw = request.POST.get('items')
            print(f"Items raw: '{items_raw}'")
            print(f"Items raw type: {type(items_raw)}")
            print(f"Items raw length: {len(items_raw) if items_raw else 'None'}")
            
            if not items_raw:
                print("ERROR: No items data received!")
                return render(request,'shop/checkout.html', {'error': 'No cart data received'})
            
            items = json.loads(items_raw)
            print(f"Items parsed: {items}")
            print(f"Items type: {type(items)}")
            print(f"Items keys: {list(items.keys()) if items else 'Empty'}")
            
            name = request.POST.get('inputName','')
            email = request.POST.get('inputEmail','')    
            address = request.POST.get('inputAddress','')
            state = request.POST.get('inputState','')
            total_raw = request.POST.get('total')
            
            print(f"Name: '{name}'")
            print(f"Email: '{email}'")
            print(f"Address: '{address}'")
            print(f"State: '{state}'")
            print(f"Total raw: '{total_raw}'")
            
            if not total_raw:
                print("ERROR: No total received!")
                return render(request,'shop/checkout.html', {'error': 'No total amount received'})
                
            total = float(total_raw)
            print(f"Total parsed: {total}")
            
            transaction_uuid = str(uuid.uuid4())
            print(f"Transaction UUID: {transaction_uuid}")
            
            tax = 0.00
            amount = f"{total:.2f}"
            tax_amount = f"{tax:.2f}"
            total_amount = f"{total + tax:.2f}"
            signed_field_names = "total_amount,transaction_uuid,product_code"
            
            print(f"Amount: {amount}")
            print(f"Tax amount: {tax_amount}")
            print(f"Total amount: {total_amount}")
            
            print("\n--- CREATING ORDER ---")
            order = Order(
                user = request.user,
                items=items, 
                name=name, 
                email=email, 
                address=address, 
                state=state,  
                total=total + tax, 
                transaction_uuid=transaction_uuid,
                has_paid=False
            )
            order.save()
            print(f"Order created successfully with ID: {order.id}")
            
            print("\n--- GENERATING SIGNATURE ---")
            data_to_sign = {
                'total_amount': total_amount,
                'transaction_uuid': transaction_uuid,
                'product_code':'EPAYTEST',
                'signed_field_names': signed_field_names
            }
            print(f"Data to sign: {data_to_sign}")
            
            signature = generate_signature(data_to_sign)
            print(f"Generated signature: {signature}")
            
            print("\n--- RENDERING ESEWA TEMPLATE ---")
            context = {
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
            }
            print(f"Context for esewa template: {context}")
            
            return render(request, "shop/esewa.html", context)
            
        except json.JSONDecodeError as e:
            print(f"JSON DECODE ERROR: {str(e)}")
            print(f"Raw items data that failed: '{items_raw}'")
            return render(request,'shop/checkout.html', {'error': f'Invalid cart data: {str(e)}'})
            
        except ValueError as e:
            print(f"VALUE ERROR (probably total conversion): {str(e)}")
            return render(request,'shop/checkout.html', {'error': f'Invalid total amount: {str(e)}'})
            
        except Exception as e:
            print(f"UNEXPECTED ERROR: {str(e)}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return render(request,'shop/checkout.html', {'error': f'Order creation failed: {str(e)}'})
    
    print("\n--- GET REQUEST ---")
    print("Rendering checkout template for GET request")
    return render(request, 'shop/checkout.html')
import requests
import xmltodict
import json
import base64
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Order
from django.contrib.auth import get_user_model
# SIMPLIFIED VERSION (Much shorter):
@login_required
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


@login_required
def view_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/orders.html', {'orders': orders})


class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'shop/signup.html'

    def form_valid(self, form):
        # Save the user instance
        user = form.save(commit=False)
        user.is_active = True  # Ensure the user is active
        user.save()
        
        # Log the user in automatically after signup
        login(self.request, user)
        
        # Add success message
        messages.success(
            self.request,
            f"Welcome, {user.email}! Your account has been created successfully."
        )
        
        # Redirect to homepage or wherever appropriate
        return redirect('index')  # or your preferred redirect destination

    def form_invalid(self, form):
        # Add error messages for invalid form submission
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"Error in {field}: {error}"
                )
        return super().form_invalid(form)

from django.contrib import messages
def login_view(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('index')  # change to your redirect URL
        else:
            return render(request, 'shop/login.html', {'form': {'errors': True}})
    
    return render(request, 'shop/login.html')


def logout_view(request):
    logout(request)
    return redirect('index')  # Change 'home' to your homepage URL name

def about(request):
    return render(request, 'shop/about.html')
def contact(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to send a message.')
            return redirect('login')
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        feedback_data = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message
        }
        # Optionally, you can append this to a list if you want to keep multiple feedbacks in memory (not persistent)
        feedback_list = []
        feedback_list.append(feedback_data)
        
        # Here you can handle the contact form submission, e.g., save to database or send an email
        messages.success(request, 'Thank you for contacting us!')
        print(f"Feedback received: {feedback_data}")
        return redirect('contact')  # Redirect to the same page or another page after submission    
    return render(request, 'shop/contact.html')
