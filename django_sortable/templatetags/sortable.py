from django import template
from django.conf import settings


register = template.Library()


SORT_ASC_CLASS = getattr(settings, 'SORT_ASC_CLASS' , 'sort-asc')
SORT_DESC_CLASS = getattr(settings, 'SORT_DESC_CLASS' , 'sort-desc')
SORT_NONE_CLASS = getattr(settings, 'SORT_DESC_CLASS' , 'sort-none')

directions = {
  'asc': {'class': SORT_ASC_CLASS, 'inverse': 'desc'}, 
  'desc': {'class': SORT_DESC_CLASS, 'inverse': 'asc'}, 
}







def parse_tag_token(token):
  """Parses a tag that's supposed to be in this format: {% sortable_link field title %}  """
  bits = [b.strip('"\'') for b in token.split_contents()]
  if len(bits) < 2:
    raise TemplateSyntaxError, "anchor tag takes at least 1 argument"
  try:
    title = bits[2]
  except IndexError:
    if bits[1].startswith(('+', '-')):
      title = bits[1][1:].capitalize()
    else:
      title = bits[1].capitalize()
  
  return (bits[1].strip(), title.strip())
  

class SortableLinkNode(template.Node):
  """Build sortable link based on query params."""
  
  def __init__(self, field_name, title, use_var_names=False):
    self.use_var_names = use_var_names
    self.default_direction = 'asc'
    self.var_names = dict()


    if use_var_names:
      self.var_names['field_name'] = field_name
      self.var_names['title'] = title
    else:
      # If we're actually passing in values
      # only change values that aren't the
      # same as the default
      self.field_name = field_name
      self.title = title

      self.process_field_name(field_name)
      
  def build_link(self, context):
    """Prepare link for rendering based on context."""
    if self.use_var_names:
      # Have to check everytime, because otherwise running through a for loop 
      # would only give us the values of the first time through
      self.default_direction = 'asc'
      self.field_name = template.Variable(self.var_names['field_name']).resolve(context)


      self.process_field_name(self.field_name)

      try:
        self.title = template.Variable(self.var_names['title']).resolve(context)
      except:
        self.title = self.var_names['title']





    get_params = context['request'].GET.copy()
    
    field_name = get_params.get('sort', None)
    if field_name:
      del(get_params['sort'])
    
    direction = get_params.get('dir', None)
    if direction:
      del(get_params['dir'])
    direction = direction if direction in ('asc', 'desc') else 'asc'
      
    # if is current field, and sort isn't defined, assume asc otherwise desc
    direction = direction or ((self.field_name == field_name) and 'asc' or 'desc')
    
    # if current field and it's sorted, make link inverse, otherwise defalut to asc
    if self.field_name == field_name:
      get_params['dir'] = directions[direction]['inverse']
    else:
      get_params['dir'] = self.default_direction
    
    if self.field_name == field_name:
      css_class = directions[direction]['class']
    else:
      css_class = SORT_NONE_CLASS
    
    params = "&%s" % (get_params.urlencode(),) if len(get_params.keys()) > 0 else ''
    url = '%s?sort=%s%s' % (context['request'].path, self.field_name, params)
    
    return (url, css_class)
    
  
  def render(self, context):
    url, css_class = self.build_link(context)
    return '<a href="%s" class="%s" title="%s">%s</a>' % (url, css_class, self.title, self.title)

  def process_field_name(self, field_name):
    self.field_name = field_name

    if field_name.startswith('-'):
      self.field_name = field_name[1:]
      self.default_direction = 'desc'
    elif field_name.startswith('+'):
      self.field_name = field_name[1:]


class SortableTableHeaderNode(SortableLinkNode):
  """Build sortable link header based on query params."""
  
  def render(self, context):
    url, css_class = self.build_link(context)
    return '<th class="%s"><a href="%s" title="%s">%s</a></th>' % (css_class, url, self.title, self.title)


class SortableURLNode(SortableLinkNode):
  """Build sortable link header based on query params."""
  
  def render(self, context):
    url, css_class = self.build_link(context)
    return url


class SortableClassNode(SortableLinkNode):
  """Build sortable link header based on query params."""
  
  def render(self, context):
    url, css_class = self.build_link(context)
    return css_class


def sortable_link(parser, token):
  field, title = parse_tag_token(token)
  return SortableLinkNode(field, title)


def sortable_vars_link(parser, token):
  var_names = token.split_contents()[1:]
  return SortableLinkNode(field_name=var_names[0], title=var_names[1], use_var_names=True)


def sortable_vars_url(parser, token):
  var_names = token.split_contents()[1:]
  return SortableURLNode(field_name=var_names[0], title=var_names[1], use_var_names=True)


def sortable_header(parser, token):
  field, title = parse_tag_token(token)
  return SortableTableHeaderNode(field, title)


def sortable_url(parser, token):
  field, title = parse_tag_token(token)
  return SortableURLNode(field, title)


def sortable_class(parser, token):
  field, title = parse_tag_token(token)
  return SortableClassNode(field, title)

  
sortable_link = register.tag(sortable_link)
sortable_header = register.tag(sortable_header)
sortable_url = register.tag(sortable_url)
sortable_class = register.tag(sortable_class)
sortable_vars_link = register.tag(sortable_vars_link)
sortable_vars_url = register.tag(sortable_vars_url)
