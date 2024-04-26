"""
views for payment gateway admin.
"""
import csv
from django.views.generic.edit import FormView
from django.contrib.auth import get_permission_codename
from django.http import HttpResponse

from openedx.custom.payment_gateway.admin.forms import AddVouchersForm
from openedx.custom.payment_gateway.models import Voucher
from openedx.custom.payment_gateway.utils import get_voucher_code


class BulkAddVouchersView(FormView):
    """
    View for adding vouchers in bulk.
    """
    template_name = 'admin/payment_gateway/add_vouchers_in_bulk.html'
    form_class = AddVouchersForm

    def _get_admin_context(self):
        """
        Build admin context.
        """
        opts = Voucher._meta
        codename = get_permission_codename('change', opts)
        has_change_permission = self.request.user.has_perm('%s.%s' % (opts.app_label, codename))
        return {
            'has_change_permission': has_change_permission,
            'opts': opts
        }

    def get_context_data(self, **kwargs):
        """
        Insert the required data into the context dict.
        """
        context = super().get_context_data(**kwargs)
        context.update(**self._get_admin_context())

        return context

    def form_valid(self, form):
        """
        If the form is valid, return the csv.
        """
        count = form.cleaned_data['count']
        name = form.cleaned_data['name']
        discount = form.cleaned_data['discount']

        vouchers = Voucher.objects.bulk_create([
            Voucher(
                name='{}. {}'.format(i, name),
                code=get_voucher_code(),
                discount=discount,
            ) for i in range(count)
        ])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={count} {name} Vouchers.csv'.format(
            count=count,
            name=name,
        )
        response = self.convert_to_csv(vouchers, response)
        return response

    @staticmethod
    def convert_to_csv(vouchers, csv_file):
        """
        Convert a list of voucher objects into a csv.
        """
        writer = csv.DictWriter(csv_file, fieldnames=['name', 'code', 'discount'])
        writer.writeheader()
        for voucher in vouchers:
            writer.writerow({
                'name': voucher.name,
                'code': voucher.code,
                'discount': voucher.discount,
            })

        return csv_file
