import logging
import utils
from os.path import join, split, getsize
from sendsecure import Safebox, Recipient, ContactMethod, Attachment, Client

def _is_attachment_allowed(extension_filter, file_extension):
    if len(file_extension) == 0:
        return False

    ext = file_extension.lower()
    if extension_filter.mode.lower() == 'forbid':
        for extention in extension_filter.list:
            if ext == extention.lower():
                return False
        return True
    else:
        for extention in extension_filter.list:
            if ext == extention.lower():
                return True
        return False

def _add_recipients(safebox, recipients):
    for r in recipients:
        recipient = Recipient(r['email'])
        if 'first_name' in r.keys():
            recipient.first_name = r['first_name']
        if 'last_name' in r.keys():
            recipient.last_name = r['last_name']
        if 'company_name' in r.keys():
            recipient.company_name = r['company_name']
        if 'contact_methods' in r.keys():
            contact_methods = r['contact_methods']
            for cm in contact_methods:
                recipient.contact_methods.append(ContactMethod(cm['destination'], cm['destination_type']))
        safebox.recipients.append(recipient);

def _encode_file_name(filename):
    if all(ord(c) < 128 for c in filename):
        return str(filename)
    return unicode(filename)

def _add_attachments(safebox, attachments, extension_filter, localpath):
    files_to_delete = []
    for a in attachments:
        if not _is_attachment_allowed(extension_filter, utils.get_file_extension(a['file_path'])):
            raise RuntimeError, 'File type "' + utils.get_file_extension(a['file_path']) + '" is not allowed by enterprise settings'
        path, filename = split(a['file_path'])
        if not path:
            path = localpath
        file_size = getsize(join(path, filename))
        attachment = Attachment(open(join(path, filename), 'rb'), str(a['content_type']), _encode_file_name(filename), file_size)
        safebox.attachments.append(attachment);
        if 'delete' not in a.keys() or a['delete']:
            files_to_delete.append(join(path, filename))
    return files_to_delete

def _apply_profile_overrides(security_profile, profile_properties):
    logger = logging.getLogger("SSFilePollerRotatingLog")
    profile_value_names = security_profile._get_value_names()
    for profile_property in profile_properties:
        if profile_property in profile_value_names:
            if security_profile.__dict__[profile_property].modifiable:
                security_profile.__dict__[profile_property].value = profile_properties[profile_property]
                logger.info('Overriding "%s" in security profile: %s', profile_property, str(profile_properties[profile_property]))
            else:
                logger.warning('"%s" override is not allowed in this security profile', profile_property)

def _set_security_profile(safebox, profile_properties, security_profiles):
    sp = None
    logger = logging.getLogger("SSFilePollerRotatingLog")
    profile_name = profile_properties['name'].lower()
    for profile in security_profiles:
        if profile_name == profile.name.lower():
            sp = profile
            logger.info('Selecting Security Profile:  "%s"', profile.name)
            break
    if sp:
        safebox.security_profile = sp
        _apply_profile_overrides(safebox.security_profile, profile_properties)
    else:
        logger.warning('Security profile "%s" was not found. Default will be used.', profile_name)

def create_safe_box(j, filename, config):
    client_config = utils.get_client_config(config)
    if 'safebox' not in j.keys():
        raise RuntimeError, 'Control file is missing the object "safebox"'
    s = j['safebox']

    if 'user_email' not in s.keys():
        raise RuntimeError, 'Control file is missing the "user_email" value'

    files_to_delete = []
    path = split(filename)[0]
    client = Client(client_config['api_token'], client_config['enterprise_account'], client_config['endpoint'], client_config['locale'])
    safebox = Safebox(s['user_email'])
    try:
        if 'subject' in s.keys():
            safebox.subject = s['subject']
        if 'message' in s.keys():
            safebox.message  = s['message']
        if 'notification_language' in s.keys():
            safebox.notification_language  = s['notification_language']
        if 'security_profile' in s.keys():
            _set_security_profile(safebox, s['security_profile'], client.get_security_profiles(s['user_email']))
        if 'recipients' in s.keys():
            _add_recipients(safebox, s['recipients'])
        if 'attachments' in s.keys():
            files_to_delete = _add_attachments(safebox, s['attachments'], client.get_enterprise_settings().extension_filter, path)
        files_to_delete.append(filename)

        logger = logging.getLogger("SSFilePollerRotatingLog")
        safe_response = client.submit_safebox(safebox);
        logger.info('SafeBox was successfully created with SafeBox ID: %s', safe_response.guid)
        return files_to_delete
    finally:
        for attachment in safebox.attachments:
            attachment.source.close()

