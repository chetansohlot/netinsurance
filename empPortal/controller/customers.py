from django.shortcuts import render,redirect
from ..models import Commission,Users, QuotationCustomer

from django.contrib.auth import authenticate, login ,logout
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def customers(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role_id == 1:
        per_page = request.GET.get('per_page', 10)
        search_field = request.GET.get('search_field', '')  # Field to search
        search_query = request.GET.get('search_query', '')  # Search value
        sorting = request.GET.get('sorting', '')  # Sorting option

        try:
            per_page = int(per_page)
        except ValueError:
            per_page = 10  # Default to 10 if invalid value is given

        # Base QuerySet
        customers = QuotationCustomer.objects.all()

        # Apply filtering
        if search_field and search_query:
            filter_args = {f"{search_field}__icontains": search_query}
            customers = customers.filter(**filter_args)

        # Apply sorting
        if sorting == "name_a_z":
            customers = customers.order_by("name")
        elif sorting == "name_z_a":
            customers = customers.order_by("-name")
        elif sorting == "recently_updated":
            customers = customers.order_by("-updated_at")
        else:
            customers = customers.order_by("-updated_at")

        total_count = customers.count()

        # Paginate results
        paginator = Paginator(customers, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'customers/customers.html', {
            'page_obj': page_obj,
            'total_count': total_count,
            'search_field': search_field,
            'search_query': search_query,
            'sorting': sorting,
            'per_page': per_page,
        })
    else:
        return redirect('login')
    
    
def create(request):
    if request.user.is_authenticated:

        products = [
            {'id': 1, 'name': 'Motor'},
            {'id': 2, 'name': 'Health'},
            {'id': 3, 'name': 'Term'},
        ]
        
        if request.user.role_id == 1:
            members = Users.objects.filter(role_id=2, activation_status='1')
        else:
            members = Users.objects.none()
    
        return render(request, 'customers/create.html', {'products': products, 'members': members})
    else:
        return redirect('login')
    
def store(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        member_id = request.POST.get('member', '').strip()
        product_id = request.POST.get('product', '').strip()
        tp_percentage = request.POST.get('tp_percentage', '').strip()
        od_percentage = request.POST.get('od_percentage', '').strip()
        net_percentage = request.POST.get('net_percentage', '').strip()

        # Validations
        if not member_id:
            messages.error(request, "Member is required.")
        if not product_id:
            messages.error(request, "Product is required.")
        if not tp_percentage or not tp_percentage.replace('.', '', 1).isdigit():
            messages.error(request, "Valid TP percentage is required.")
        if not od_percentage or not od_percentage.replace('.', '', 1).isdigit():
            messages.error(request, "Valid OD percentage is required.")
        if not net_percentage or not net_percentage.replace('.', '', 1).isdigit():
            messages.error(request, "Valid Net percentage is required.")

        # Check if this sub-broker already has a commission for the selected insurer
        if Commission.objects.filter(member_id=member_id, product_id=product_id).exists():
            messages.error(request, "You already have a commission for this member & product.")

        # If any errors, redirect back to the 'add-commission' page
        if messages.get_messages(request):
            return redirect('add-commission')

        # Save to database
        Commission.objects.create(
            product_id=product_id,
            member_id=member_id,
            tp_percentage=float(tp_percentage),
            od_percentage=float(od_percentage),
            net_percentage=float(net_percentage),
            created_by=request.user.id
        )


        messages.success(request, "Commission added successfully.")
        return redirect('commissions')

    else:
        messages.error(request, "Invalid request.")
        return redirect('add-commission')