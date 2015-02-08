=================
Django OfferMaker
=================

``django-offermaker`` library is a solution for Django applications, which allows
to create *multi variant offers* and use them on your site.

*Multi variant offer* is a structure which defines dependencies between values for
given set of fields.

Eg. for the fields **credit contribution** and **number of instalments** we
have the following dependencies:

    * for **0%** credit contribution, it is required to have maximum **12**
      instalments,
    * for **10%+** contribution, it is allowed to have **12-24** instalments,
    * and for **20%+** contribution, it is allowed to have **12-36** instalments.

Functions of ``django-offermaker``
----------------------------------

    * Create and edit *multi variant offer* by using **Offermaker Admin Editor**.
    * Display *multi variant offer* in tabular way by using **Offermaker Template
      Tag**.
    * Display form which dynamically adjusts to user filled values based on
      *multi variant offer* by using **OfferMakerFormView Generic View**.
    * Make decision which variant of *multi variant offer* is suitable for
      given parameters by using **decide helper**.


Changelog
---------

* 0.9.8

    * Selenium test for offermaker admin editor and offermaker form and bug fixes
      in supported Django and Python versions.

* 0.9.7

    * Added Class Based View for offermaker form
    * Added decide() method

* 0.9.5

    * Small bug fixes

* 0.9.4

    * Django 1.7 support
    * Python 3 support



Support
-------

* Environments: Python 2.6, Python 2.7, Python 3.2, Python 3.3, Python 3.4, PyPy,
* Django versions: Django 1.5, Django 1.6, Django 1.7 (Python 2.6 is not supported),


Demo application
----------------

1. You can check it online http://offermaker.kjw.pt

2. Or checkout and install locally::

    git clone git@github.com:kkujawinski/django-offermaker-demo.git


Quick start
-----------
1. Install django-offermaker ::

    pip install django-offermaker

2. Site configuration in settings.py ::

      INSTALLED_APPS = (
          ...
          'offermaker',
      )

3. Create Django form with needed fields::

    from django import forms

    class MyForm(forms.Form):
        product = forms.ChoiceField(
            label='Product',
            choices=(
                ('', '---'), ('PROD1', 'Product X'), ('PROD2', 'Product Y'), ('PROD3', 'Product Z'),
            ),
            required=False)
        crediting_period = forms.ChoiceField(
            label='Crediting period',
            choices=(('', '---'), ('12', '12'), ('24', '24'), ('36', '36'), ('48', '48')))
        interest_rate = forms.FloatField(label='Interest rate', min_value=1, max_value=5)
        contribution = forms.FloatField(label='Contribution', min_value=0)

        # # Uncomment for Django 1.5
        # def __init__(self, *args, **kwargs):
        #     super(MyForm, self).__init__(*args, **kwargs)
        #     self.fields['interest_rate'].widget.attrs['data-om-type'] = 'number'
        #     self.fields['interest_rate'].widget.attrs['data-om-min'] = 1
        #     self.fields['interest_rate'].widget.attrs['data-om-max'] = 5
        #     self.fields['contribution'].widget.attrs['data-om-type'] = 'number'
        #     self.fields['contribution'].widget.attrs['data-om-min'] = 0

4. Define your offer (in case you do not store it in database)::

    offer = {
        'params': {},
        'variants': [[
            {
                'params': {
                    'crediting_period': ['24'],
                    'product': ['PROD1']
                }
            }, {
                'params': {
                    'crediting_period': ['12', '36', '48'],
                    'product': ['PROD2']
                }
            }, {
                'params': {
                    'product': ['PROD3']
                }
            }
        ], [
            {
                'params': {
                    'contribution': [[10, 20]],
                    'interest_rate': [[2, 2]],
                    'product': ['PROD1']
                }
            }, {
                'params': {
                    'contribution': [[30, 40]],
                    'interest_rate': [[4, 4]],
                    'product': ['PROD1']
                }
            }, {
                'params': {
                    'contribution': [[30, 70]],
                    'interest_rate': [[5, 5]],
                    'product': ['PROD2', 'PROD3']
                }
            }
        ]]
    }

5. Offer form:

a) Use dispatcher code in Django view ::

    import offermaker

    class MyOfferFormView(offermaker.OfferMakerFormView):
        form_class = MyForm
        offermaker_offer = offer
        template_name = 'my_offer_form_view.html'

    my_offer_form_view = MyOfferFormView.as_view()


b) Initialize offerform in template ::

    <head>
    {% load offermaker %}
    <script type="text/javascript" src="http://code.jquery.com/jquery-1.10.2.min.js"></script>
    {% offermaker_javascript %}
    </head>

    <body>

    <form action="?" method="post" id="offer_form">
        <div class="alert-placeholder" style="height: 30px;"></div>
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Submit</button>
    </form>


    <script type="text/javascript">
        (function() {
            $('#offer_form').offer_form();
        })();
    </script>

6. Offer preview with Offermaker Template Tag

a) Pass offer form object from view to template::

    class MyOfferPreviewView(TemplateView):
        template_name = 'offer_preview.html'

        def get_context_data(self):
            output = super(MyOfferPreviewView, self).get_context_data()
            output['offer'] = offermaker.OfferMakerCore(MyForm, offer)
            return output


b) Use proper template tag in template to print table::

    {% load offermaker %}

    {% offermaker_preview offer %}


7. Offermaker Admin Editor:

a) Use OfferJSONField field in your model. Remember to pass your django form created in 3.::

    import offermaker

    class MyOfferMakerField(offermaker.OfferJSONField):
        form_object = MyForm()

    class MyOffer(models.Model):
        id = models.AutoField(primary_key=True)
        name = models.CharField(max_length=30)
        offer = MyOfferMakerField()

b) Create your own Admin Site for model::

    import models

    class OfferAdmin(admin.ModelAdmin):
        list_display = ('name',)
        search_fields = ('name', 'user')
        fields = ('name', 'offer')

        # # Uncomment for Django 1.5
        # class Media:
        #     js = ('//code.jquery.com/jquery-1.11.0.min.js',)


    admin.site.register(models.Offer, OfferAdmin)

7. Decide helper::

    core_object = offermaker.OfferMakerCore(MyForm, offer)

    result = core_object.decide({'crediting_period': 24})
    print(result['product'].items)
    # frozenset({'PROD1', 'PROD3'})
    print(result['interest_rate'].ranges)
    # frozenset({(4, 4), (5, 5), (2, 2)})
    print(result['contribution'].ranges)
    # frozenset({(10, 20), (30, 70)})

    result = core_object.decide({'crediting_period': 24, 'interest_rate': 2})
    print(result['product'].fixed)
    # PROD1



Basic customization
-------------------

1. Using offers stored in database:

a) you need to pass proper offer object to Offermaker in form/preview view::

    offer = MyOffer.objects.filter(id=request.GET['id']).first()
    core_object = offermaker.OfferMakerCore(MyForm, offer.offer)

b) and configure proper params to be used in ajax requests::

    $('#offer_form').offer_form({
        ajax_extra_params: function(params) {
            return { id: {{ request.GET.id }} };
        },
    });


2. Substituting builtin formatters for infotip and error alerts::

    $('#offer_form').offer_form({
        error_alert_factory: function (msg) {
            var $error = $('<p class="error"><span>' + msg + '</span></p>');
            $('.alert-placeholder', $form).append($error);
            return $error;
        },
        tooltip_factory: function ($field, msg) {
            var $tooltip = $('<p class="infotip">' + msg + '</p>');
            $field.parent().append($tooltip);
            return $tooltip;
        }
    });

3. Use builtin formatters for Twitter Bootstap3::

    (function() {
        $('#offer_form').offer_form({
            bootstrap3: true,
        });
    })();

4. Customizing messages::

    (function() {
        $('#offer_form').offer_form({
            msgs: {
                'NO_VARIANTS': 'No matching variants',
                'INFO_ITEMS': 'Available values are: %s.',
                'INFO_FIXED': 'Only available value is %s.',
                'RANGE_left': 'to %2$s',
                'RANGE_right': 'from %1$s',
                'RANGE_both': 'from %1$s to %2$s',
                'AND': ' and '
            },
            iteration_str: function (items) {
                return items.slice(0, -2).concat(items.slice(-2).join(msgs.AND)).join(', ');
            }
        });
    })();

5. Creating preview table for certain fields::

    {% offermaker_preview offer fields='product, crediting_period' %}


6. Add html attributes to generated preview table::

    {% offermaker_preview offer class='table table-bordered' %}
