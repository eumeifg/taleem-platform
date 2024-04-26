""" Live class API """


from openedx.core.djangoapps.waffle_utils import WaffleSwitch, WaffleSwitchNamespace

WAFFLE_SWITCH_NAMESPACE = WaffleSwitchNamespace(name='live_course_list_api_rate_limit')

USE_RATE_LIMIT_2_FOR_LIVE_COURSE_LIST_API = WaffleSwitch(WAFFLE_SWITCH_NAMESPACE, 'rate_limit_2')
USE_RATE_LIMIT_10_FOR_LIVE_COURSE_LIST_API = WaffleSwitch(WAFFLE_SWITCH_NAMESPACE, 'rate_limit_10')

