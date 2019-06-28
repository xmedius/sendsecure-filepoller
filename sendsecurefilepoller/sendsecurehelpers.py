import logging
from os.path import join, split, getsize, isfile, abspath, isabs
from sendsecure import Safebox, ContactMethod, Attachment, Client, Participant
from utils import get_client_config, get_file_extension, is_file_writable

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
        recipient = Participant(email=r['email'])
        if 'first_name' in r.keys():
            recipient.first_name = r['first_name']
        if 'last_name' in r.keys():
            recipient.last_name = r['last_name']
        if 'company_name' in r.keys():
            recipient.guest_options.company_name = r['company_name']
        if 'contact_methods' in r.keys():
            contact_methods = r['contact_methods']
            for cm in contact_methods:
                cmethod = ContactMethod({'destination': cm['destination'], 'destination_type': cm['destination_type']})
                recipient.guest_options.contact_methods.append(cmethod)
        safebox.participants.append(recipient)

def _prepare_attachements_path(attachments, localpath):
    logger = logging.getLogger("SSFilePollerRotatingLog")
    for a in attachments:
        filename = a['file_path']
        if not isabs(filename):
            filename = abspath(join(localpath, filename))
        logger.info('Attachement: %s', filename)
        if not isfile(filename):
            raise RuntimeError('Attachement: ' + filename + ', was not found')
        if not is_file_writable(filename):
            raise RuntimeError('Attachement: ' + filename + ', cannot be delete')
        a['file_path'] = filename

def _add_attachments(safebox, extension_filter, localpath):
    logger = logging.getLogger("SSFilePollerRotatingLog")
    attachments = safebox.attachments
    safebox.attachments = []
    files_to_delete = []
    for a in attachments:
        if not _is_attachment_allowed(extension_filter, get_file_extension(a['file_path'])):
            raise RuntimeError('File type "' + get_file_extension(a['file_path']) + '" is not allowed by enterprise settings')
        path, filename = split(a['file_path'])
        file_size = getsize(a['file_path'])
        attachment = Attachment({'source':open(a['file_path'], 'rb'), 'content_type':str(a['content_type']), 'filename':str(filename), 'size':file_size})
        safebox.attachments.append(attachment)
        if 'delete' not in a.keys() or a['delete']:
            files_to_delete.append(a['file_path'])
    return files_to_delete

def _set_security_profile_id(safebox, profile_name, security_profiles):
    sp = None
    logger = logging.getLogger("SSFilePollerRotatingLog")
    for profile in security_profiles:
        if profile_name.lower() == profile.name.lower():
            safebox.security_profile_id = profile.id
            sp = profile
            logger.info('Selecting Security Profile:  "%s"', profile.name)
            break

    if sp is None:
        logger.warning('Security profile "%s" was not found. Default will be used.', profile_name)

def create_safe_box(j, filename, config):
    logger = logging.getLogger("SSFilePollerRotatingLog")
    client_config = get_client_config(config)
    if 'safebox' not in j.keys():
        raise RuntimeError('Control file is missing the object "safebox"')

    files_to_delete = []
    path = split(filename)[0]
    client = Client(client_config)
    try:
        safebox = Safebox(params=j['safebox'])
        _prepare_attachements_path(safebox.attachments, path)

        if hasattr(safebox, 'security_profile_name'):
            _set_security_profile_id(safebox, safebox.security_profile_name, client.get_security_profiles(safebox.user_email))
        if len(safebox.attachments) > 0:
            files_to_delete = _add_attachments(safebox, client.get_enterprise_settings().extension_filter, path)
        files_to_delete.append(filename)

        safe_response = client.submit_safebox(safebox)
        logger.info('SafeBox was successfully created with SafeBox ID: %s', safe_response.guid)
        return files_to_delete
    finally:
        for attachment in safebox.attachments:
            if hasattr(attachment, 'source'):
                attachment.source.close()
