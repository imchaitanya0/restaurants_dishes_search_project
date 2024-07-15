from django.shortcuts import render
from django.db.models import Q
from .models import MenuItem

def search_view(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = MenuItem.objects.filter(
            Q(item_name__icontains=query)
        ).select_related('restaurant').order_by('-restaurant__user_rating_aggregate')[:10]
    return render(request, 'search_results.html', {'results': results, 'query': query})