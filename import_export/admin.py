from __future__ import with_statement

import os
import tempfile
from eav.models import Attribute
from datetime import datetime
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.conf.urls import patterns, url
from django.template.response import TemplateResponse
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from import_export import fields
from .forms import (
        ImportForm,
        ConfirmImportForm,
        ExportForm,
        )
from .resources import (
        modelresource_factory,
        )
from .formats import base_formats

from copy import deepcopy
DEFAULT_FORMATS = (
            base_formats.CSV,
            base_formats.XLS,
            base_formats.XLSX,
            base_formats.TSV,
            base_formats.ODS,
            base_formats.JSON,
            base_formats.YAML,
            base_formats.HTML,
            )


class ImportMixin(object):
    """
    Import mixin.
    """

    change_list_template = 'admin/import_export/change_list_import.html'
    import_template_name = 'admin/import_export/import.html'
    resource_class = None
    formats = DEFAULT_FORMATS
    from_encoding = "cp1251"

    def get_urls(self):
        urls = super(ImportMixin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        my_urls = patterns('',
            url(r'^process_import/$',
                self.admin_site.admin_view(self.process_import),
                name='%s_%s_process_import' % info),
            url(r'^import/$',
                self.admin_site.admin_view(self.import_action),
                name='%s_%s_import' % info),
        )
        return my_urls + urls

    def get_resource_class(self):
        if not self.resource_class:
            return modelresource_factory(self.model)
        else:
            return self.resource_class

    def get_import_formats(self):
        """
        Returns available import formats.
        """
        return [f for f in self.formats]

    #changed her, and all places, where used
    def update_resource_class(self, resource):
        for attr in Attribute.objects.all():
            if 'price_field' in attr.options and 'dependent' not in attr.options['price_field']:  #dependent problem CHANGE HER
                slug=attr.slug
                field=fields.Field()
                field.column_name=attr.name_en
                field.attribute=slug
                setattr(resource, slug, field)
                def dehidrator(attr_slug):
                    def dehidr(obj):
                        try:
                            return getattr(obj,attr_slug)
                        except AttributeError:
                            return _('no field')
                    return dehidr
                setattr(resource, 'dehydrate_'+attr.slug, deepcopy(dehidrator(slug)))
                resource.fields[slug]=getattr(resource,slug)

        return resource

    def process_import(self, request, *args, **kwargs):
        '''
        Perform the actuall import action (after the user has confirmed he wishes to import)
        '''
        opts = self.model._meta
        resource = self.get_resource_class()()
        resource= self.update_resource_class(resource)

        confirm_form = ConfirmImportForm(request.POST)
        if confirm_form.is_valid():
            import_formats = self.get_import_formats()
            input_format = import_formats[
                    1
                    ]()
            import_file = open(confirm_form.cleaned_data['import_file_name'],
                    input_format.get_read_mode())
            data = import_file.read()
            if not input_format.is_binary() and self.from_encoding:
                data = unicode(data, self.from_encoding).encode('utf-8')
            dataset = input_format.create_dataset(data)

            resource.import_data(dataset, dry_run=False,
                    raise_errors=True)

            success_message = _('Import finished')
            messages.success(request, success_message)
            import_file.close()

            url = reverse('admin:%s_%s_changelist' %
                               (opts.app_label, opts.module_name),
                               current_app=self.admin_site.name)
            return HttpResponseRedirect(url)

    def import_action(self, request, *args, **kwargs):
        '''
        Perform a dry_run of the import to make sure the import will not result in errors.
        If there where no error, save the the user uploaded file to a local temp file that 
        will be used by 'process_import' for the actual import.
        '''
        resource = self.get_resource_class()()
        resource= self.update_resource_class(resource)
        context = {}

        import_formats = self.get_import_formats()
        form = ImportForm(import_formats,
                request.POST or None,
                request.FILES or None)

        if request.POST and form.is_valid():
            #changed
            file_name=form.cleaned_data['import_file'].name
            if file_name[-3:]=='xls':
                input_format = import_formats[1]()
            elif file_name[-3:]=='csv':
                input_format = import_formats[0]()
            else:
                input_format = import_formats[2]()
            import_file = form.cleaned_data['import_file']
            import_file.open(input_format.get_read_mode())
            data = import_file.read()
            if not input_format.is_binary() and self.from_encoding:
                data = unicode(data, self.from_encoding).encode('utf-8')
            #changed
            #if  import_formats[int(form.cleaned_data['input_format'])]==base_formats.CSV:
            #    data=data.replace(';',',')
            dataset = input_format.create_dataset(data)
            result = resource.import_data(dataset, dry_run=True,
                    raise_errors=False)

            context['result'] = result

            if not result.has_errors():
                LogEntry.objects.log_action(
                    user_id         = 1,
                    content_type_id = None,
                    object_id       = None,
                    object_repr     = 'prices imported',
                    action_flag     = CHANGE
                )
                tmp_file = tempfile.NamedTemporaryFile(delete=False)
                tmp_file.write(data)
                tmp_file.close()
                context['confirm_form'] = ConfirmImportForm(initial={
                    'import_file_name': tmp_file.name,
                    'input_format': 0,
                    })

        context['form'] = form
        context['opts'] = self.model._meta
        context['fields'] = [f.column_name for f in resource.get_fields()]



        return TemplateResponse(request, [self.import_template_name],
                context, current_app=self.admin_site.name)


class ExportMixin(object):
    """
    Export mixin.
    """
    resource_class = None
    change_list_template = 'admin/import_export/change_list_export.html'
    export_template_name = 'admin/import_export/export.html'
    formats = DEFAULT_FORMATS
    to_encoding = "cp1251"

    def get_urls(self):
        urls = super(ExportMixin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        my_urls = patterns('',
            url(r'^export/$',
                self.admin_site.admin_view(self.export_action),
                name='%s_%s_export' % info),
        )
        return my_urls + urls

    def get_resource_class(self):
        if not self.resource_class:
            return modelresource_factory(self.model)
        else:
            return self.resource_class

    def get_export_formats(self):
        """
        Returns available import formats.
        """
        return [f for f in self.formats if f().can_export()]

    def get_export_filename(self, file_format):
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = "%s-%s.%s" % (self.model.__name__,
                date_str,
                file_format.get_extension())
        return filename

    def get_export_queryset(self, request):
        """
        Returns export queryset.

        Default implementation respects applied search and filters.
        """
        # copied from django/contrib/admin/options.py
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)

        ChangeList = self.get_changelist(request)
        cl = ChangeList(request, self.model, list_display,
            list_display_links, self.list_filter, self.date_hierarchy,
            self.search_fields, self.list_select_related,
            self.list_per_page, self.list_max_show_all, self.list_editable,
            self)

        return cl.query_set

    #changed
    def export_action(self, request, *args, **kwargs):
        formats = self.get_export_formats()
        form = ExportForm(formats, request.POST or None)
        if 1:
            file_format = formats[1
                    ]()

            resource_class = self.get_resource_class()
            resource= self.update_resource_class(resource_class())
            queryset = self.get_export_queryset(request)
            data = resource_class().export(queryset)
            #changed
            file = file_format.export_data(data)
            response = HttpResponse(
                file,
                mimetype='application/octet-stream',
                )
            response['Content-Disposition'] = 'attachment; filename=%s' % (
                   self.get_export_filename(file_format),
                   )
            return response

        context = {}
        context['form'] = form
        context['opts'] = self.model._meta
        return TemplateResponse(request, [self.export_template_name],
                context, current_app=self.admin_site.name)


class ImportExportMixin(ImportMixin, ExportMixin):
    """
    Import and export mixin.
    """
    change_list_template = 'admin/import_export/change_list_import_export.html'


class ImportExportModelAdmin(ImportExportMixin, admin.ModelAdmin):
    """
    Subclass of ModelAdmin with import/export functionality.
    """
