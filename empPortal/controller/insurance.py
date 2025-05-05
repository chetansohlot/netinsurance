from django.shortcuts import render, redirect
from django.contrib import messages
from ..model import Insurance
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def insurance_list(request):
    insurance_qs = Insurance.objects.all().order_by('-created_at')

    total_count = insurance_qs.count()
    active_count = insurance_qs.filter(active='1').count()  # '1' means active
    inactive_count = insurance_qs.filter(active='0').count()  # '0' means inactive

    return render(request, 'insurance/insurance_index.html',
                  {
                      'insurance_qs': insurance_qs,
                      'total_count': total_count,
                      'active_count': active_count,
                      'inactive_count': inactive_count,
                  })


def insurance_create(request):
    if request.method == 'POST':
        insurance_company = request.POST.get('insurance_company')
        active = request.POST.get('active', '1')  # Default to active if no value provided

        # Save to the database
        Insurance.objects.create(
            insurance_company=insurance_company,
            active=active
        )
        messages.success(request, 'Insurance created successfully.')
        return redirect('insurance_index')

    return render(request, 'insurance/insurance_create.html')

def insurance_edit(request, insurance_id):
    insurance = get_object_or_404(Insurance, id=insurance_id)
    if request.method == 'POST':
        insurance.insurance_company = request.POST.get('insurance_company')
        #insurance.active = request.POST.get('active', '1')  # Default to active if no value provided
        messages.success(request, 'Insurance updated successfully.')
        insurance.save()

        return redirect('insurance_index')

    return render(request, 'insurance/insurance_create.html', {'insurance': insurance})

#Anjali
def toggle_insurance_status(request, insurance_id):
    insurance = get_object_or_404(Insurance, id=insurance_id)

    if insurance.active == '1':
        insurance.active = '0'
        messages.info(request, 'Insurance deactivated successfully.')
    else:
        insurance.active = '1'
        messages.success(request, 'Insurance activated successfully.')

    insurance.save()
    return redirect('insurance_index')  # Update with your actual list page name