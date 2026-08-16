from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render

from apps.core.decorators import business_owner_required

from .forms import BusinessForm, OwnerPasswordChangeForm
from .services import update_business_information


@business_owner_required
def settings(request):
    business = request.user.business
    form = BusinessForm(request.POST or None, request.FILES or None, instance=business)
    if request.method == "POST" and form.is_valid():
        update_business_information(business, form.cleaned_data)
        messages.success(request, "Informations du commerce enregistrées.")
        return redirect("businesses:settings")
    return render(
        request,
        "dashboard/commerce/form.html",
        {"form": form, "business": business},
    )


@business_owner_required
def password_change(request):
    form = OwnerPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Mot de passe modifié.")
        return redirect("businesses:password_change")
    return render(
        request,
        "dashboard/password/form.html",
        {"form": form},
    )
