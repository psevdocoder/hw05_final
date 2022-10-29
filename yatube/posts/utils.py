from django.core.paginator import Paginator

MAX_POSTS_ON_PAGE = 10


def get_page_context(queryset, request):
    paginator = Paginator(queryset, MAX_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
