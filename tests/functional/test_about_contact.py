"""About page and Contact page (info panel, branch tabs, form validation, routing)."""

import re

import pytest
from playwright.sync_api import expect

from pages.about_page import AboutPage
from pages.contact_page import ContactPage


@pytest.mark.tc("TC-113", "TC-123")
def test_about_page_heading_story_and_principles(page, site):
    about = AboutPage(page).open()
    expect(about.heading).to_have_text(re.compile(r"\S"))
    expect(about.principles_heading).to_be_visible()
    assert about.principles.count() >= 3
    expect(about.location_links).to_have_count(len(site.branches))


@pytest.fixture
def contact(page) -> ContactPage:
    return ContactPage(page).open()


@pytest.mark.tc("TC-011")
@pytest.mark.parametrize("city", ["Benin City", "Ikeja", "Lagos", "Lekki", "Owerri"])
def test_branch_tab_shows_address_and_map(contact: ContactPage, site, city):
    b = site.branch(city)
    contact.branch_tab(city).click()
    expect(contact.main).to_contain_text(b.address)
    expect(contact.map_frame).to_be_visible()
    expect(contact.routing).to_contain_text(b.name)


@pytest.mark.tc("TC-011")
@pytest.mark.defect("BUG-007")
def test_branch_tab_shows_hours_phone_and_email(contact: ContactPage):
    expect(contact.info_note).to_have_count(0)
    for label in ("Phone", "Email", "Hours"):
        expect(contact.main.get_by_text(label, exact=True)).to_be_visible(timeout=2000)


@pytest.mark.tc("TC-045")
def test_contact_form_mandatory_validation(contact: ContactPage):
    contact.send.click()
    for msg in (
        "Enter your name",
        "Enter a valid email",
        "Enter a valid phone number",
        "Tell us a little more",
    ):
        expect(contact.main.get_by_text(msg)).to_be_visible()


@pytest.mark.tc("TC-045")
def test_routing_heading_follows_selected_tab(contact: ContactPage, site):
    for b in site.branches:
        contact.branch_tab(b.city).click()
        expect(contact.routing).to_have_text(re.compile(rf"Going to {re.escape(b.name)}"))


@pytest.mark.tc("TC-045")
def test_contact_privacy_link_works(page, contact: ContactPage):
    assert page.request.get(contact.privacy_link.get_attribute("href")).status == 200


@pytest.mark.live_write
@pytest.mark.tc("TC-012")
def test_contact_form_submits_valid_message(contact: ContactPage):
    contact.name.fill("Ada Obi (QA automation)")
    contact.email.fill("ada-qa@maildrop.cc")
    contact.phone.fill("+2348012345678")
    contact.subject.fill("Automated test - please ignore")
    contact.message.fill("Automated regression test message. Please ignore.")
    contact.send.click()
    expect(contact.main.get_by_text(re.compile(r"(sent|received|thank)", re.I))).to_be_visible(timeout=15000)


@pytest.mark.live_write
@pytest.mark.security
@pytest.mark.tc("TC-057")
def test_contact_form_script_injection_not_executed(contact: ContactPage):
    fired = []
    contact.page.on("dialog", lambda d: (fired.append(d.message), d.dismiss()))
    contact.name.fill("<script>alert(1)</script>")
    contact.email.fill("xss-qa@maildrop.cc")
    contact.phone.fill("+2348012345678")
    contact.message.fill("<img src=x onerror=alert(1)> automated security test, please ignore")
    contact.send.click()
    contact.page.wait_for_timeout(2000)
    assert not fired
