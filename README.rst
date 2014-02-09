===========
Offer Maker
===========

Demo application
----------------

1. You can check it online http://offermaker.kjw.pt

2. Or checkout and install locally::

    git clone git@bitbucket.org:kkujawinski/offer-maker-demo-site.git


Quick start
-----------
1. Install django-offermaker ::

    pip install django-offermaker

2. Site configuration in settings.py ::

      INSTALLED_APPS = (
          ...
          'offermaker',
      )

3. Create Django form::

    from django import forms

    class MyForm(forms.Form):
        product = forms.ChoiceField(
            label=u'Product',
            choices=(
                ('', '---'), ('PROD1', 'Product X'), ('PROD2', 'Product Y'), ('PROD3', 'Product Z'),
            ),
            required=False)
        crediting_period = forms.ChoiceField(
            label=u'Crediting period',
            choices=(('', '---'), ('12', '12'), ('24', '24'), ('36', '36'), ('48', '48')))
        interest_rate = forms.FloatField(label=u'Interest rate', min_value=1, max_value=5)
        contribution = forms.FloatField(label=u'Contribution', min_value=0)

4. Define your offer (in case you do not store it in database)::

    offer = {
        'variants': [
            [{
                'params': {'product': 'PROD1', 'crediting_period': ['24']},
            }, {
                'params': {'product': 'PROD2'},
                'variants': [
                    {'params': {'crediting_period': ['12']}},
                    {'params': {'crediting_period': ['36']}},
                    {'params': {'crediting_period': ['48']}}]
            }, {
                'params': {'product': 'PROD3'},
            }],
            [{
                'params': {'product': 'PROD1'},
                'variants': [
                    {'params': {'contribution': (10, 20), 'interest_rate': (2, 2)}},
                    {'params': {'contribution': (30, 40), 'interest_rate': (4, 4)}}]
            }, {
                'params': {'product': ['PROD2', 'PROD3']},
                'variants': [{
                    'params': {'contribution': (30, 70), 'interest_rate': (5, 5)}
                }]
            }]
        ]
    }

5. Offer form:

a) Use dispatcher code in Django view ::

    import offermaker

    def my_form_view(request):
        core_object = offermaker.OfferMakerCore(DemoOfferMakerForm, offer)

        def handler_get(form):
            return render(request, 'my_form.html', ({'form': form})

        def handler_post(form):
            if form.is_valid():
                return HttpResponseRedirect('success')
            return handler_get(form)

        dispatcher = offermaker.OfferMakerDispatcher.from_core_object(handler_get, handler_post, core_object=core_object)
        return dispatcher.handle_request(request)


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

6. Offer preview:

a) Pass offerform object from view to template::

    def my_form_view(request):
        core_object = offermaker.OfferMakerCore(DemoOfferMakerForm, offer)

b) Use proper template tag in template to print table::

    {% load offermaker %}

    {% offermaker_preview offer %}


7. Offer editor:

a) Use OfferJSONField field in your model. Remember to pass your django form created in 3.::

    import offermaker

    class MyOffer(models.Model):
        id = models.AutoField(primary_key=True)
        name = models.CharField(max_length=30)
        offer = offermaker.OfferJSONField(form_object=MyForm())

b) Create your own Admin Site for model::

    import models

    class OfferAdmin(admin.ModelAdmin):
        list_display = ('name',)
        search_fields = ('name', 'user')
        fields = ('name', 'offer')

    admin.site.register(models.Offer, OfferAdmin)


Basic customization
-------------------

1. Using offers stored in database:

a) you need to pass proper offer object to Offermaker in form/preview view::

    offer = MyOffer.objects.filter(id=request.GET['id']).first()
    core_object = offermaker.OfferMakerCore(DemoOfferMakerForm, offer.offer)

b) and configure proper params to be used ajax requests::

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
