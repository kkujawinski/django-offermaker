# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import time

from django.contrib.auth.models import User
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.test import LiveServerTestCase

from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

from . import models


class FunctionalTests(LiveServerTestCase):
    urls = 'offermaker.tests2.urls'
    static_handler = StaticFilesHandler

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(FunctionalTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(FunctionalTests, cls).tearDownClass()

    def test_fields_values_switch(self):
        def input_help_text(input_element):
            try:
                input_element = input_element._el
            except AttributeError:
                pass
            return input_element.find_element_by_xpath('..').find_element_by_css_selector('p.infotip').text

        self.selenium.get('%s%s' % (self.live_server_url, '/form/'))

        product_select = Select(self.selenium.find_element_by_name("product"))
        crediting_period_select = Select(self.selenium.find_element_by_name("crediting_period"))
        interest_rate_input = self.selenium.find_element_by_name("interest_rate")
        contribution_input = self.selenium.find_element_by_name("contribution")

        self.assertEqual(input_help_text(product_select), 'Available values are: Product X, Product Y and Product Z.')
        self.assertEqual(input_help_text(crediting_period_select), 'Available values are: 12, 24, 36 and 48.')
        self.assertEqual(input_help_text(interest_rate_input), 'Available values are: 2, 4 and 5.')
        self.assertEqual(input_help_text(contribution_input), 'Available values are: from 10 to 20 and from 30 to 70.')

        # Autofill other elements 1
        product_select.select_by_visible_text('Product X')
        self.assertEqual(input_help_text(product_select), 'Available values are: Product X and Product Z.')
        self.assertEqual(crediting_period_select.first_selected_option.text, '24')
        self.assertEqual(input_help_text(crediting_period_select), 'Available values are: 24.')
        self.assertEqual(input_help_text(contribution_input), 'Available values are: from 10 to 20 and from 30 to 40.')

        # Autofill other elements 2
        interest_rate_input.send_keys('2', '\t')
        self.assertEqual(input_help_text(product_select), 'Available values are: Product X.')
        self.assertEqual(input_help_text(contribution_input), 'Available values are: from 10 to 20.')

        # Breaking variant
        product_select.select_by_visible_text('Product Y')

        alert = self.selenium.switch_to.alert
        self.assertEqual(alert.text, 'Are you sure to break current variant?')
        alert.accept()

        self.assertEqual(input_help_text(product_select), 'Available values are: Product Y and Product Z.')

        self.assertEqual(crediting_period_select.first_selected_option.text, '---')
        self.assertEqual(input_help_text(crediting_period_select), 'Available values are: 12, 36 and 48.')
        self.assertEqual(interest_rate_input.get_attribute('value'), '5')
        self.assertEqual(input_help_text(interest_rate_input), 'Only available value is 5.')
        self.assertEqual(input_help_text(contribution_input), 'Available values are: from 30 to 70.')
        self.assertEqual(input_help_text(contribution_input), 'Available values are: from 30 to 70.')

        # Value not matching any variant
        contribution_input.send_keys('80', '\t')
        self.assertRaises(NoAlertPresentException, self.selenium.switch_to.alert.accept)
        self.assertEqual(
            self.selenium.find_element_by_css_selector('.alert-placeholder .error span').text,
            'No matching variants'
        )

        # No matching variants
        contribution_input.clear()
        contribution_input.send_keys('10', '\t')

        alert = self.selenium.switch_to.alert
        self.assertEqual(alert.text, 'Are you sure to break current variant?')
        alert.dismiss()

        self.assertEqual(
            self.selenium.find_element_by_css_selector('.alert-placeholder .error span').text,
            'No matching variants'
        )

    def admin_login(self):
        # from offermaker.tests2.models import MyOffer
        User.objects.create_superuser(username='admin', password='123', email='')

        self.selenium.get('%s%s' % (self.live_server_url, '/admin/'))
        self.selenium.find_element_by_name("username").send_keys('admin')
        self.selenium.find_element_by_name("password").send_keys('123')
        self.selenium.find_element_by_xpath('.//input[@type="submit"]').click()

    def create_new_offer_view(self):
        # self.selenium.find_element_by_xpath('.//table//tr[th[@scope="row"]/a/text()="My offers"]')
        # self.selenium.find_element_by_css_selector('tr.model-myoffer a.addlink').click()
        self.selenium.find_element_by_xpath('.//table//tr[th[@scope="row"]/a/text()="My offers"]/td/a[@class="addlink"]').click()

    def test_admin_offer_editor_removing_fields(self):
        self.admin_login()
        self.create_new_offer_view()

        add_group_link = self.selenium.find_element_by_css_selector('.group_addlink a.addlink')
        add_group_link.click()
        add_group_link.click()

        self.selenium.find_element_by_name('selector__1__product').click()

        group_1_add_variant_link = self.selenium.find_element_by_css_selector('.group_1 .offermaker_summary a.addlink')
        group_1_add_variant_link.click()
        group_1_add_variant_link.click()

        self.selenium.find_element_by_css_selector('#field__1-0__product-tokenfield')
        self.selenium.find_element_by_css_selector('#field__1-1__product-tokenfield')

        # removing variants
        self.selenium.find_element_by_css_selector('.group_1 .offermaker_table .variant__1-0 a.deletelink').click()

        self.assertRaises(NoSuchElementException, self.selenium.find_element_by_css_selector, '#field__1-0__product-tokenfield')

        # adding new variant after removal
        group_1_add_variant_link.click()

        self.selenium.find_element_by_css_selector('#field__1-2__product-tokenfield')

        # removing group of variants
        self.selenium.find_element_by_css_selector('.group_1 .group_deletelink a.deletelink').click()

        self.assertRaises(NoSuchElementException, self.selenium.find_element_by_css_selector, '.group_1')

        # adding new group of variants after removal
        add_group_link.click()

        self.selenium.find_element_by_css_selector('.group_3')

        self.selenium.find_element_by_css_selector('.group_2 .group_deletelink a.deletelink').click()
        self.selenium.find_element_by_css_selector('.group_3 .group_deletelink a.deletelink').click()

    def test_admin_offer_editor(self):
        def select_by_text(field, label):
            field.send_keys(label)
            time.sleep(0.1)
            field.send_keys(Keys.ARROW_DOWN, '\t')

        self.admin_login()
        self.create_new_offer_view()

        # CREATE OFFER
        self.selenium.find_element_by_name("name").send_keys('XYZ')

        add_group_link = self.selenium.find_element_by_css_selector('.group_addlink a.addlink')
        add_group_link.click()
        add_group_link.click()

        self.selenium.find_element_by_name('selector__1__product').click()
        self.selenium.find_element_by_name('selector__1__crediting_period').click()

        self.selenium.find_element_by_name('selector__2__product').click()
        self.selenium.find_element_by_name('selector__2__contribution').click()
        self.selenium.find_element_by_name('selector__2__interest_rate').click()

        group_1_add_variant_link = self.selenium.find_element_by_css_selector('.group_1 .offermaker_summary a.addlink')
        group_1_add_variant_link.click()
        group_1_add_variant_link.click()
        group_1_add_variant_link.click()

        select_by_text(self.selenium.find_element_by_css_selector('#field__1-0__product-tokenfield'), 'Product X')
        self.selenium.find_element_by_css_selector('#field__1-0__crediting_period-tokenfield').send_keys('24', '\t')
        select_by_text(self.selenium.find_element_by_css_selector('#field__1-1__product-tokenfield'), 'Product Y')
        self.selenium.find_element_by_css_selector('#field__1-1__crediting_period-tokenfield').send_keys('12', '\t', '36', '\t', '48', '\t')
        select_by_text(self.selenium.find_element_by_css_selector('#field__1-2__product-tokenfield'), 'Product Z')

        group_2_add_variant_link = self.selenium.find_element_by_css_selector('.group_2 .offermaker_summary a.addlink')
        group_2_add_variant_link.click()
        group_2_add_variant_link.click()
        group_2_add_variant_link.click()
        select_by_text(self.selenium.find_element_by_css_selector('#field__2-0__product-tokenfield'), 'Product X')

        # checking if ranges will be marged
        self.selenium.find_element_by_css_selector('#field__2-0__contribution-tokenfield').send_keys('10:15', '\t', '14:20', '\t')
        self.selenium.find_element_by_css_selector('#field__2-0__interest_rate-tokenfield').send_keys('2', '\t')

        select_by_text(self.selenium.find_element_by_css_selector('#field__2-1__product-tokenfield'), 'Product X')
        self.selenium.find_element_by_css_selector('#field__2-1__contribution-tokenfield').send_keys('30:40')
        self.selenium.find_element_by_css_selector('#field__2-1__interest_rate-tokenfield').send_keys('4', '\t')

        select_by_text(self.selenium.find_element_by_css_selector('#field__2-2__product-tokenfield'), 'Product Y')
        select_by_text(self.selenium.find_element_by_css_selector('#field__2-2__product-tokenfield'), 'Product Z')

        # checking if token will be created on field's focus out
        self.selenium.find_element_by_css_selector('#field__2-2__contribution-tokenfield').send_keys('30:70')
        self.selenium.find_element_by_css_selector('#field__2-2__interest_rate-tokenfield').send_keys('5', '\t')

        self.selenium.find_element_by_name('_save').click()

        expected_offer = {
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

        saved_offer = models.MyOffer.objects.get(name='XYZ').offer

        self.assertEqual(saved_offer, expected_offer)
