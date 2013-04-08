import time
import urllib2
# import simplejson
from django.utils import simplejson
import math
import datetime


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



   
