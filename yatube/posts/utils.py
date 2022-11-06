from django.core.paginator import Paginator
from yatube.settings import QUANTITY
# QUANTITY = 10


def pages(request, args):
    paginator = Paginator(args, QUANTITY)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
