import time
import urllib2
import json
import unicodedata
import re


# import simplejson
from django.utils import simplejson
import math
import datetime
from datetime import timedelta
from django.utils.safestring import mark_safe

def school_is_partner(email):
    # get list of approved emails
    emails = json.loads(f.open('partner_emails.json').read())
    stub = email.split("@")[1]
    if stub in emails:
        return True
    return False

def _get_json(url):
        """ returns JSON file in Python-readable format from URL"""
        sys.stdout.write("fetching " + url + "\n")
        try:
            return json.load(urllib2.urlopen(url))
        except urllib.URLError, e:
            print str(e)
        except:
            return None

def _formatted_date(date):

    now = datetime.datetime.now()
    one_day = timedelta(days=1)
    two_days = timedelta(days=2)

    if (now - date) < one_day:
         return_date = "Today at "
    elif (now - date) < two_days:
        return_date = "Yesterday at "
    else:
        return date

    if date.minute < 10:
        minute = "0" + str(date.minute)
    else:
        minute = str(date.minute)

    if date.hour > 12:
        hour = str(date.hour - 12)
        prefix = " p.m."
    elif date.hour == 0:
        hour = "12"
        prefix = " a.m."
    else:
        hour = str(date.hour)
        prefix = " a.m."

    print date.hour
    return return_date + hour + ":" + minute + prefix
  

def _months_from_now_json(start_date):
    ## expects a start-date as a string of form MM/YY

    now = datetime.datetime.now()
    start_mo = int(start_date[:2])
    start_yr = int(start_date[3:])

    end_mo = now.month
    end_yr = int(str(now.year)[2:])
    
    return (12 * (end_yr - start_yr)) + (end_mo - start_mo)


# Returns # months difference between start_date and now
def _months_from_now(start_date):

    now = datetime.datetime.now()
    return (12 * (now.year - start_date.year)) + (now.month - start_date.month)

# Takes a python datetime obj and returns a string of format MM/YY
def _format_date(date):

    month = str(date.month)
    if len(month) == 1:
        return "0" + month + "/" + str(date.year)[2:]
    else:
        return month + "/" + str(date.year)[2:]

# taken straight from viz.js
def _months_difference(start_mo, start_yr, end_mo, end_yr, compress, round):
    diff = 12 * (end_yr - start_yr)
    diff += end_mo - start_mo

    if compress:
        diff /= 2
        if round == 'upper':
            diff = math.ceil(diff)
        if round == 'lower':
            diff = math.floor(diff)

    return diff

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        excpetions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry

# Imports (added @ top): 
# import unicodedata
# import re
# from django.utils.safestring import mark_safe
#   also, bugs when strings are input so I coerce to unicode, prob a better way to do this
def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    From django
    """
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return mark_safe(re.sub('[-\s]+', '-', value))

   
