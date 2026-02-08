from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.template.loader import get_template
from django.db.models import Q
from decimal import Decimal
from xhtml2pdf import pisa
import uuid
from django.shortcuts import get_object_or_404

from .models import Product, Bill, BillItem

def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('create_bill')
        return render(request, 'store/login.html', {'error': 'Invalid credentials'})
    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
@login_required
def create_bill(request):
    products = Product.objects.all()

    if request.method == "POST":
        subtotal = Decimal("0.00")
        cart = []

        for product in products:
            qty = int(request.POST.get(f"qty_{product.id}", 0))
            if qty > 0:
                total = product.price * qty
                subtotal += total
                cart.append((product, qty, total))

        cgst = subtotal * Decimal("0.09")
        sgst = subtotal * Decimal("0.09")
        grand = subtotal + cgst + sgst

        bill = Bill.objects.create(
            bill_no=f"BILL-{uuid.uuid4().hex[:6]}",
            customer_name=request.POST['customer'],
            mobile=request.POST['mobile'],
            subtotal=subtotal,
            cgst=cgst,
            sgst=sgst,
            grand_total=grand
        )

        for product, qty, total in cart:
            BillItem.objects.create(
                bill=bill,
                product_name=product.name,
                price=product.price,
                quantity=qty,
                total=total
            )
            product.stock -= qty
            product.save()

        return redirect('bill_pdf', bill_no=bill.bill_no)

    return render(request, 'store/create_bill.html', {'products': products})
@login_required
def bill_history(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    q = request.GET.get('q')
    bills = Bill.objects.all().order_by('-date')

    if q:
        bills = bills.filter(
            Q(bill_no__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(mobile__icontains=q)
        )

    return render(request, 'store/bill_history.html', {'bills': bills})
@login_required
def cancel_bill(request, bill_no):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    bill = Bill.objects.get(bill_no=bill_no)
    if bill.is_cancelled:
        return redirect('bill_history')

    for item in bill.items.all():
        product = Product.objects.get(name=item.product_name)
        product.stock += item.quantity
        product.save()

    bill.is_cancelled = True
    bill.save()
    return redirect('bill_history')
@login_required
def bill_pdf(request, bill_no):
    bill = Bill.objects.get(bill_no=bill_no)
    template = get_template('store/invoice.html')
    html = template.render({'bill': bill})
    response = HttpResponse(content_type='application/pdf')
    pisa.CreatePDF(html, dest=response)
    return response


@login_required
def product_list(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Admins only")

    products = Product.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products
    })
@login_required
def product_add(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Admins only")

    if request.method == "POST":
        Product.objects.create(
            name=request.POST['name'],
            price=request.POST['price'],
            stock=request.POST['stock']
        )
        return redirect('product_list')

    return render(request, 'store/product_add.html')
@login_required
def product_edit(request, product_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Admins only")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST['name']
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        product.save()
        return redirect('product_list')

    return render(request, 'store/product_edit.html', {
        'product': product
    })
