from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from .compat import parse_bits
from ..cachefiles import ImageCacheFile
from ..registry import generator_registry
from modifier.models import ImageSpecModel
from django.conf import settings
from django.utils.safestring import SafeText, SafeUnicode
import platform
from django.core.files.images import ImageFile
from os.path import join, exists
from django.contrib.sites.models import Site

register = template.Library()
ASSIGNMENT_DELIMETER = 'as'
HTML_ATTRS_DELIMITER = '--'
DEFAULT_THUMBNAIL_GENERATOR = 'imagekit:thumbnail'


def get_cachefile(context, generator_id, generator_kwargs, source=None):
    generator_id = generator_id.resolve(context)
    kwargs = dict((k, v.resolve(context)) for k, v in generator_kwargs.items())

    #changed
    if type(kwargs['source'])==SafeText or type(kwargs['source'])==str or type(kwargs['source'])==unicode or type(kwargs['source'])==SafeUnicode:
	kwargs['source']=str(kwargs['source']).strip()
        if platform.system() == 'Linux':
            f_path=settings.PROJECT_PATH+kwargs['source']
            if exists(f_path):
                with open(f_path,'rb') as f:
                    source=ImageFile(f)
            else:
                with open(join(settings.PROJECT_PATH, kwargs['source']),'rb') as f:
                    source=ImageFile(f)
        else:
            f_path=settings.PROJECT_PATH+kwargs['source'].replace('/','\\')
            if exists(f_path):
                with open(f_path,'rb') as f:
                    source=ImageFile(f)
            else:
                with open(join(settings.PROJECT_PATH, kwargs['source'].replace('/','\\')),'rb') as f:
                    source=ImageFile(f)
        kwargs['source']=source
    ##

    generator = generator_registry.get(generator_id, **kwargs)
    return ImageCacheFile(generator)


def parse_dimensions(dimensions):
    """
    Parse the width and height values from a dimension string. Valid values are
    '1x1', '1x', and 'x1'. If one of the dimensions is omitted, the parse result
    will be None for that value.

    """
    width, height = [d.strip() and int(d) or None for d in dimensions.split('x')]
    return dict(width=width, height=height)


class GenerateImageAssignmentNode(template.Node):

    def __init__(self, variable_name, generator_id, generator_kwargs):
        self._generator_id = generator_id
        self._generator_kwargs = generator_kwargs
        self._variable_name = variable_name

    def get_variable_name(self, context):
        return unicode(self._variable_name)

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        variable_name = self.get_variable_name(context)
        context[variable_name] = get_cachefile(context, self._generator_id,
                self._generator_kwargs)
        return ''


class GenerateImageTagNode(template.Node):

    def __init__(self, generator_id, generator_kwargs, html_attrs):
        self._generator_id = generator_id
        self._generator_kwargs = generator_kwargs
        self._html_attrs = html_attrs

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        file = get_cachefile(context, self._generator_id,
                self._generator_kwargs)
        attrs = dict((k, v.resolve(context)) for k, v in
                self._html_attrs.items())

        # Only add width and height if neither is specified (to allow for
        # proportional in-browser scaling).
        if not 'width' in attrs and not 'height' in attrs:
            attrs.update(width=file.width, height=file.height)
        if 'title' in attrs and attrs['title']==u"copy_alt":
            attrs['title']=attrs['alt']
        if 'title' in attrs:
            attrs['title']=attrs['title'].replace('[company]', Site.objects.get_current().company)
            attrs['title']=attrs['title'].replace('[country]', Site.objects.get_current().country)
        
        if 'alt' in attrs:
            attrs['alt']=attrs['alt'].replace('[company]', Site.objects.get_current().company)
            attrs['alt']=attrs['alt'].replace('[country]', Site.objects.get_current().country)        
        
        attrs['src'] = file.url
        attr_str = ' '.join('%s="%s"' % (escape(k), escape(v)) for k, v in
                attrs.items())
        if 'no_tag' in attrs:
            return mark_safe(attrs['src'])
        return mark_safe(u'<img %s />' % attr_str)


class ThumbnailAssignmentNode(template.Node):

    def __init__(self, variable_name, generator_id, dimensions, source, generator_kwargs):
        self._variable_name = variable_name
        self._generator_id = generator_id
        self._dimensions = dimensions
        self._source = source
        self._generator_kwargs = generator_kwargs

    def get_variable_name(self, context):
        return unicode(self._variable_name)

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        variable_name = self.get_variable_name(context)

        generator_id = self._generator_id.resolve(context) if self._generator_id else DEFAULT_THUMBNAIL_GENERATOR
        kwargs = dict((k, v.resolve(context)) for k, v in
                self._generator_kwargs.items())
        kwargs['source'] = self._source
        kwargs.update(parse_dimensions(self._dimensions.resolve(context)))
        generator = generator_registry.get(generator_id, **kwargs)

        context[variable_name] = ImageCacheFile(generator)

        return ''


class ThumbnailImageTagNode(template.Node):

    def __init__(self, generator_id, dimensions, source, generator_kwargs, html_attrs):
        self._generator_id = generator_id
        self._dimensions = dimensions
        self._source = source
        self._generator_kwargs = generator_kwargs
        self._html_attrs = html_attrs

    def render(self, context):
        from ..utils import autodiscover
        autodiscover()

        generator_id = self._generator_id.resolve(context) if self._generator_id else DEFAULT_THUMBNAIL_GENERATOR
        dimensions = parse_dimensions(self._dimensions.resolve(context))
        kwargs = dict((k, v.resolve(context)) for k, v in
                self._generator_kwargs.items())
        kwargs['source'] = self._source
        kwargs.update(dimensions)
        generator = generator_registry.get(generator_id, **kwargs)

        file = ImageCacheFile(generator)

        attrs = dict((k, v.resolve(context)) for k, v in
                self._html_attrs.items())

        # Only add width and height if neither is specified (to allow for
        # proportional in-browser scaling).
        if not 'width' in attrs and not 'height' in attrs:
            attrs.update(width=file.width, height=file.height)
        
        if 'title' in attrs and attrs['title']==u"copy_alt":
            attrs['title']=attrs['alt']
            
        if 'title' in attrs:
            attrs['title']=attrs['title'].replace('[company]', Site.objects.get_current().company)
            attrs['title']=attrs['title'].replace('[country]', Site.objects.get_current().country)
        
        if 'alt' in attrs:
            attrs['alt']=attrs['alt'].replace('[company]', Site.objects.get_current().company)
            attrs['alt']=attrs['alt'].replace('[country]', Site.objects.get_current().country)    
        
        attrs['src'] = file.url
        attr_str = ' '.join('%s="%s"' % (escape(k), escape(v)) for k, v in
                attrs.items())
        return mark_safe(u'<img %s />' % attr_str)


def parse_ik_tag_bits(parser, bits):
    """
    Parses the tag name, html attributes and variable name (for assignment tags)
    from the provided bits. The preceding bits may vary and are left to be
    parsed by specific tags.

    """
    varname = None
    html_attrs = {}
    tag_name = bits.pop(0)

    if len(bits) >= 2 and bits[-2] == ASSIGNMENT_DELIMETER:
        varname = bits[-1]
        bits = bits[:-2]

    if HTML_ATTRS_DELIMITER in bits:

        if varname:
            raise template.TemplateSyntaxError('Do not specify html attributes'
                    ' (using "%s") when using the "%s" tag as an assignment'
                    ' tag.' % (HTML_ATTRS_DELIMITER, tag_name))

        index = bits.index(HTML_ATTRS_DELIMITER)
        html_bits = bits[index + 1:]
        bits = bits[:index]

        if not html_bits:
            raise template.TemplateSyntaxError('Don\'t use "%s" unless you\'re'
                ' setting html attributes.' % HTML_ATTRS_DELIMITER)

        args, html_attrs = parse_bits(parser, html_bits, [], 'args',
                'kwargs', None, False, tag_name)
        if len(args):
            raise template.TemplateSyntaxError('All "%s" tag arguments after'
                    ' the "%s" token must be named.' % (tag_name,
                    HTML_ATTRS_DELIMITER))

    return (tag_name, bits, html_attrs, varname)


#@register.tag
def generateimage(parser, token):
    """
    Creates an image based on the provided arguments.

    By default::

        {% generateimage 'myapp:thumbnail' source=mymodel.profile_image %}

    generates an ``<img>`` tag::

        <img src="/path/to/34d944f200dd794bf1e6a7f37849f72b.jpg" width="100" height="100" />

    You can add additional attributes to the tag using "--". For example,
    this::

        {% generateimage 'myapp:thumbnail' source=mymodel.profile_image -- alt="Hello!" %}

    will result in the following markup::

        <img src="/path/to/34d944f200dd794bf1e6a7f37849f72b.jpg" width="100" height="100" alt="Hello!" />

    For more flexibility, ``generateimage`` also works as an assignment tag::

        {% generateimage 'myapp:thumbnail' source=mymodel.profile_image as th %}
        <img src="{{ th.url }}" width="{{ th.width }}" height="{{ th.height }}" />

    """
    bits = token.split_contents()

    tag_name, bits, html_attrs, varname = parse_ik_tag_bits(parser, bits)

    args, kwargs = parse_bits(parser, bits, ['generator_id'], 'args', 'kwargs',
            None, False, tag_name)

    if len(args) != 1:
        raise template.TemplateSyntaxError('The "%s" tag requires exactly one'
                ' unnamed argument (the generator id).' % tag_name)

    #changed
    generator_id = args[0]
    generator_id_str=generator_id.resolve([])
    if generator_id_str not in generator_registry._generators:
        generator_registry.register(generator_id_str, ImageSpecModel.objects.get(name=generator_id_str).get_image_spec_class())
    ###

    if varname:
        return GenerateImageAssignmentNode(varname, generator_id, kwargs)
    else:
        return GenerateImageTagNode(generator_id, kwargs, html_attrs)


#@register.tag
from django.template import FilterExpression
def thumbnail(parser, token):
    """
    A convenient shortcut syntax for generating a thumbnail. The following::

        {% thumbnail '100x100' mymodel.profile_image %}

    is equivalent to::

        {% generateimage 'imagekit:thumbnail' source=mymodel.profile_image width=100 height=100 %}

    The thumbnail tag supports the "--" and "as" bits for adding html
    attributes and assigning to a variable, respectively. It also accepts the
    kwargs "anchor", and "crop".

    To use "smart cropping" (the ``SmartResize`` processor)::

        {% thumbnail '100x100' mymodel.profile_image %}

    To crop, anchoring the image to the top right (the ``ResizeToFill``
    processor)::

        {% thumbnail '100x100' mymodel.profile_image anchor='tr' %}

    To resize without cropping (using the ``ResizeToFit`` processor)::

        {% thumbnail '100x100' mymodel.profile_image crop=0 %}

    """
    bits = token.split_contents()

    tag_name, bits, html_attrs, varname = parse_ik_tag_bits(parser, bits)

    args, kwargs = parse_bits(parser, bits, [], 'args', 'kwargs',
            None, False, tag_name)

    if len(args) < 2:
        raise template.TemplateSyntaxError('The "%s" tag requires at least two'
                ' unnamed arguments: the dimensions and the source image.'
                % tag_name)
    elif len(args) > 3:
        raise template.TemplateSyntaxError('The "%s" tag accepts at most three'
                ' unnamed arguments: a generator id, the dimensions, and the'
                ' source image.' % tag_name)

    dimensions, presource = args[-2:]
    generator_id = args[0] if len(args) > 2 else None
    if type(presource)==FilterExpression:
		presource=presource.var
    if type(presource)==SafeText or type(presource)==str or type(presource)==unicode or type(presource)==SafeUnicode:
    		presource=str(presource)
    		if platform.system() == 'Linux':
    			f_path=settings.PROJECT_PATH+presource
    			if exists(f_path):
    				with open(f_path,'rb') as f:
    					source=ImageFile(f)
    			else:
    				with open(join(settings.PROJECT_PATH, presource),'rb') as f:
    					source=ImageFile(f)
    		else:
    			f_path=settings.PROJECT_PATH+presource.replace('/','\\')
    			if exists(f_path):
    				with open(f_path,'rb') as f:
    					source=ImageFile(f)
    			else:
    				with open(join(settings.PROJECT_PATH, presource.replace('/','\\')),'rb') as f:
    					source=ImageFile(f)
    else:
    	source=presource
    if varname:
        return ThumbnailAssignmentNode(varname, generator_id, dimensions,
                source, kwargs)
    else:
        return ThumbnailImageTagNode(generator_id, dimensions, source, kwargs,
                html_attrs)


generateimage = register.tag(generateimage)
thumbnail = register.tag(thumbnail)
