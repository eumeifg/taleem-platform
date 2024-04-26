"""
Utility functions for taleem_organizaition app.
"""
from ipware.ip import get_ip

from openedx.custom.taleem_organization.models import (
    College, Department, OrganizationType, Subject, TaleemOrganization, Skill, TashgeelAuthToken, TashgheelConfig
)
from openedx.custom.taleem.models import Ta3leemUserProfile
from openedx.custom.taleem_organization.exceptions import TashgheelAPIError


def get_subjects():
    """
    Get a list of available subjects.
    """
    return Subject.objects.values_list('name', flat=True).all()


def get_organizations():
    """
    Get a list of available organizations.
    """
    organizations = {
        OrganizationType.SCHOOL.name: [],
        OrganizationType.UNIVERSITY.name: [],
    }

    for record in TaleemOrganization.objects.all():
        organizations[record.type].append(record.name)

    return organizations


def get_colleges(university):
    """
    Get a list of available colleges for the given university.

    Arguments:
        university (str): Name of the university.
    """
    return College.objects.filter(
        organization__name=university,
        organization__type=OrganizationType.UNIVERSITY.name,
    ).values('id', 'name').all()


def get_departments(university, college):
    """
    Get a list of available departments for the given college in the given university.

    Arguments:
        university (str): Name of the university.
        college (str): Name of the college.
    """
    college = College.objects.get(
        name=college,
        organization__name=university,
        organization__type=OrganizationType.UNIVERSITY.name,
    )
    return Department.objects.filter(
        college=college,
    ).values('id', 'name').all()


def get_colleges_by_organization_id(organization_id):
    """
        Get a list of available colleges for the given organization.

        Arguments:
            university (str): Name of the university.
        """
    return College.objects.filter(
        organization__id=organization_id,
        organization__type=OrganizationType.UNIVERSITY.name,
    ).values('id', 'name').all()


def get_departments_by_college_id(college_id, university_id):
    """
    Get a list of available departments for the given college in the given university.

    Arguments:
        university (str): Name of the university.
        college (str): Name of the college.
    """
    college = College.objects.get(
        id=college_id,
        organization__id=university_id,
        organization__type=OrganizationType.UNIVERSITY.name,
    )
    return Department.objects.filter(
        college=college,
    ).values('id', 'name').all()


def skill_name_exists(skill):
    """
    Check if the given skill name exists in the system or not.

    Arguments:
        skill (str): Name of the skill to check.

    Returns:
        (bool): True if skill name exists in the system, False otherwise.
    """
    return Skill.objects.filter(name=skill).exists()


def get_tashgheel_user(email, username):
    """
    Get tashgheel user with given email or username.

    Arguments:
        email (str): Email of the tashgeel User.
        username (str): Username of the tashgeel User.

    Returns:
        (User): Djangi user object with given email or user name.
    """
    ta3leem_user_profile = Ta3leemUserProfile.objects.filter(user__email=email, is_tashgheel_user=True).first()
    if ta3leem_user_profile:
        return ta3leem_user_profile.user

    ta3leem_user_profile = Ta3leemUserProfile.objects.filter(user__username=username, is_tashgheel_user=True).first()
    if ta3leem_user_profile:
        return ta3leem_user_profile.user


def get_token(token):
    """
    Get Tashgeel Auth Token or None if token is not found.

    Arguments:
        token (str): String form of token UUID

    Returns:
        (TashgeelAuthToken | None): Instance of the TashgeelAuthToken or None if not not found.
    """
    return TashgeelAuthToken.objects.filter(token=token).first()


def has_token(token):
    """
    Check if Tashgeel Auth Token exists in the database

    Arguments:
        token (str): String form of token UUID

    Returns:
        (Boolean): True if Tashgeel Auth Token exists in the database, False otherwise.
    """
    return TashgeelAuthToken.objects.filter(token=token).exists()


def delete_token(token):
    """
    Delete the Tashgeel Auth Token from the database

    Arguments:
        token (str): String form of token UUID
    """
    return TashgeelAuthToken.objects.filter(token=token).delete()


def create_token(user):
    """
    Create a return Tashgeel Auth Token.

    Arguments:
        (user): Django user.
    """
    token, _ = TashgeelAuthToken.objects.get_or_create(user=user)
    return token


def validate_tashgheel_access(request):
    """
    Validate the request has proper rights else raise TashgheelAPIError.
    """
    tashgheel_config = TashgheelConfig.current()

    if tashgheel_config.enabled:
        if 'Authorization' in request.headers:
            token = request.headers.get('Authorization', '').strip() or ''
            if not token.endswith(tashgheel_config.token):
                raise TashgheelAPIError('Invalid Token Provided. Please see the Tashgheel config.')
        ip_address = get_ip(request)
        if ip_address not in str(tashgheel_config.ip_addresses):
            raise TashgheelAPIError(
                'IP address [{}] is not added in config. Please see the Tashgheel config.'.format(ip_address)
            )
    return True  # User has access
