
import base64
import io
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen

import pytz
import unicodecsv
from dateutil import tz
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import get_language
from PIL import Image

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_site


BAGHDAD_TIMEZONE = tz.gettz(settings.TIME_ZONE)

log = logging.getLogger(__name__)


def local_datetime_to_utc_datetime(datetime):
    """
    Convert the given datetime to UTC. Considering the local_timezone is Asia/Baghdad.
    """
    local_datetime = datetime.replace(tzinfo=BAGHDAD_TIMEZONE)
    return local_datetime.astimezone(pytz.utc)


def utc_datetime_to_local_datetime(datetime):
    """
    Convert the given datetime(UTC) to local time local_timezone is Asia/Baghdad.
    """
    utc_datetime = datetime.replace(tzinfo=pytz.UTC)
    return utc_datetime.astimezone(BAGHDAD_TIMEZONE)


def timedelta_to_hhmmss(td):
    """
    Given the timedelta it will return a
    string in format "x days, HH:MM:SS"
    """
    mm, ss = divmod(td.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = "%02d:%02d:%02d" % (hh, mm, ss)
    if td.days:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""
        s = ("%d day%s, " % plural(td.days)) + s
    return s


def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K


def parse_csv(file_stream):
    """
    Parse csv file and return a stream of dictionaries representing each row.
    First line of CSV file must contain column headers.
    Arguments:
         file_stream: input file
    Yields:
        dict: CSV line parsed into a dictionary.
    """
    try:
        reader = unicodecsv.DictReader(file_stream, encoding="utf-8-sig")
    except (unicodecsv.Error, UnicodeDecodeError) as error:
        raise ValidationError("Unable to parse CSV file. Please make sure it is a CSV 'utf-8' encoded file.")

    # "yield from reader" would be nicer, but we're on python2.7 yet.
    for row in reader:
        yield row


def convert_comma_separated_string_to_list(comma_separated_string):
    """
    Convert the comma separated string to a valid list.
    """
    return list(set(item.strip() for item in comma_separated_string.split(",") if item.strip()))


def dedupe(items, key=None):
    """
    Remove duplicates from the items list.
    """
    seen, unique_items = set(), []
    key = key if key is not None else lambda _item: _item

    for item in items:
        _key = key(item)

        # Perform case in-sensitive checks
        _key = to_lower(_key)
        if _key not in seen:
            unique_items.append(item)
            seen.add(_key)

    return unique_items


def to_lower(value):
    """
    Convert the value to lower case if possible. This function does not raise error if value is not of correct type.
    """
    if isinstance(value, str):
        return value.lower()
    return value


def format_date_time(date_time):
    """
    Format datetime to a generic format.

    Arguments:
        date_time (datetime): A Date time object
    """
    return date_time.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_minutes_from_time_duration(time_duration):
    """
    Get number of minutes from a time duration.

    Arguments:
        time_duration (str): Time duration in the form of HH:MM (H is Hour and M is Minute).
    """
    if not isinstance(time_duration, str):
        raise TypeError('Invalid argument type, must be "str" found "{}"".'.format(type(time_duration)))

    try:
        hours, minutes = time_duration.split(':')
    except ValueError:
        raise ValueError('Invalid time duration format, valid format is HH:MM (H is Hour and M is Minute).')
    else:
        if not all([hours.strip(), minutes.strip()]):
            raise ValueError('Invalid time duration format, valid format is HH:MM (H is Hour and M is Minute).')

    try:
        hours = int(hours)
        minutes = int(minutes)
    except ValueError:
        raise ValueError('Invalid time duration format, valid format is HH:MM (H is Hour and M is Minute).')

    return hours * 60 + minutes


def send_email(recipients, subject, message, html_message=None):
    """
    Send an email to one or more users.
    """
    recipient_list = [recipients] if isinstance(recipients, str) else recipients

    email_from = settings.EMAIL_HOST_USER

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')

    msg['From'] = email_from
    msg['Subject'] = subject

    # Create the body of the message (a plain-text and an HTML version).
    # Record the MIME types of both parts - text/plain and text/html.
    if message:
        part1 = MIMEText(message, 'plain')
        msg.attach(part1)
    if html_message:
        part2 = MIMEText(html_message, 'html')
        msg.attach(part2)

    # Send the message via local SMTP server.
    mail = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=20)

    if settings.EMAIL_USE_TLS:
        mail.starttls()

    mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    mail.sendmail(settings.EMAIL_HOST_USER, recipient_list, msg.as_string())
    mail.quit()


def convert_image_to_base64(image_url):
    """
    Convert the given image into the base64 string.
    """
    log.info("Converting the image [{}] in base64".format(image_url))

    # converting the remote image into Pillow Image object
    image = Image.open(urlopen(image_url))

    # Saving the image in memory in bytes.
    in_memory_image = io.BytesIO()
    image.save(in_memory_image, format="PNG")

    # reset file pointer to start
    in_memory_image.seek(0)

    # Converting the image from Bytes to Base64
    return base64.b64encode(in_memory_image.read()).decode('utf-8')


def get_email_context():
    site = get_current_site()

    message_context = get_base_template_context(site)
    message_context.update({'dashboard_url': '{}/dashboard'.format(settings.LMS_ROOT_URL)})
    message_context.update({
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'registration_link': '{lms_root_url}/register'.format(
            lms_root_url=configuration_helpers.get_value('lms_root_url', settings.LMS_ROOT_URL))
    })

    return message_context


def get_sms_body_for_login(user_language_pref):
    """
    Return the sms body for 2FA according to current language preference.
    """
    message_body = "Please insert the following Pin to proceed to your Ta3leem portal. {code}"
    current_language_pref = get_language()
    if current_language_pref == 'ar' or user_language_pref == 'ar':
        message_body = "{code} الرجاء إدخال الرمز التالي للدخول الى حسابك في منصة تعليم"
    return message_body
