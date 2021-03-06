from configparser import ConfigParser, MissingSectionHeaderError
import logging
import codecs
from logging.handlers import RotatingFileHandler
from time import strftime, sleep
from os import stat, mkdir, rename, listdir, remove, fspath
from os.path import isfile, join, splitext, split, dirname, exists

logger = None

class MyRotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            path,filename = split(self.baseFilename)
            for i in range(self.backupCount - 1, 0, -1):
                sfn = join(path, "%d.%s" % (i, filename))
                dfn = join(path, "%d.%s" % (i+1, filename))
                if exists(sfn):
                    if exists(dfn):
                        remove(dfn)
                    rename(sfn, dfn)
            dfn = join(path, '1.' + filename)
            if exists(dfn):
                remove(dfn)
            if exists(self.baseFilename):
                rename(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()

def get_file_extension(filename):
    file_extension = splitext(filename)[1]
    if file_extension.startswith("."):
        return file_extension[1:]
    return file_extension

def move_to_failed_subfolder(filepath):
    basepath, filename = split(filepath)
    basepath = join(basepath, 'Failed')
    try:
        stat(basepath)
    except:
        mkdir(basepath)
    logger = logging.getLogger("SSFilePollerRotatingLog")
    new_file = join(basepath, strftime("%Y%m%d-%H%M%S") + '-' +filename)
    logger.warning('Moving file "%s" to "%s"', filename, new_file)
    rename(filepath, new_file)

def get_config(section_name):
    try:
        localpath = dirname(__file__)
        config = ConfigParser()
        config.read_file(codecs.open(join(localpath, 'config.ini'), 'r', 'utf-8'))
        dict1 = {}
        options = config.options(section_name)
        for option in options:
            dict1[option] = config.get(section_name, option)
        return dict1
    except MissingSectionHeaderError as e:
        print('Config is missing Section Header:')
        print('  This can be caused by a BOM introduced in config file')
        print('  First line of the config file :\n\t', e.line.encode('utf-8'), '\n')
    raise RuntimeError("Could not read config")

def get_config_value_with_default(config, value_name, default_value):
    try:
        return config[value_name].strip()
    except:
        return default_value

def get_client_config(config):
    dict1 = {}
    if 'enterprise_account' not in config.keys():
        raise RuntimeError('"enterprise_account" setting is missing in config.ini')
    if 'api_token' not in config.keys():
        raise RuntimeError('"api_token" setting is missing in config.ini')
    dict1['enterprise_account'] = config['enterprise_account'].strip()
    if not dict1['enterprise_account']:
        raise RuntimeError('"enterprise_account" setting is not configured in config.ini')
    dict1['token'] = config['api_token'].strip()
    if not dict1['token']:
        raise RuntimeError('"api_token" setting is not configured in config.ini')
    dict1['endpoint'] = get_config_value_with_default(config, 'endpoint', 'https://portal.xmedius.com')
    dict1['locale'] =  get_config_value_with_default(config, 'locale', 'en')
    return dict1

def _parse_source_file(f, filename):
    if get_file_extension(filename).lower() == 'json':
        import json
        return json.load(f)
    else:
        """
        Custom parsing could be implemented here, as long as the returned data structure is
        the same as the one returned by the JSON parser's load method (dictionary of tuples).
        That way, no modifications would be required in the rest of the code.
        """
        raise RuntimeError('Unknown file format')

def process_file_job(filepath, config):
    logger = logging.getLogger("SSFilePollerRotatingLog")
    logger.info('/--PROCESSING FILE JOB...')
    logger.info('File name is: %s', filepath)

    from sendsecurehelpers import create_safe_box
    try:
        files_to_delete = []
        f = codecs.open(filepath,'rb')
        try:
            done = False
            source_data = _parse_source_file(f, filepath)
            files_to_delete = create_safe_box(source_data, filepath, config)
            done = True
        except Exception as e:
            if f:
                f.close()
                f = None
            logger.error('File job processing error: %s (%s)', filepath, str(e))
            move_to_failed_subfolder(filepath)
        finally:
            if f:
                f.close()
                f = None
            if done:
                for file in files_to_delete:
                    remove_file(file)
    except Exception as e:
        logger.error('Failed to access file: %s (%s)', filepath, str(e))
    logger.info('\--PROCESSING FILE JOB...DONE!')

def _is_a_sendsecure_filejob(filepath):
    if isfile(filepath):
        if get_file_extension(filepath).lower() == 'json':
            if is_file_writable(filepath):
                return True
            else:
                logger.warning('Skipping: "%s", file is not writable', filepath)
    return False

def process_jobs_in_folder(config):
    source_path = config['source_path'].strip()
    try:
        stat(source_path)
    except:
        mkdir(source_path)

    polling_interval = int(get_config_value_with_default(config, 'polling_interval', '5'))
    files = [f for f in listdir(source_path) if _is_a_sendsecure_filejob(join(source_path, f))]
    if not files:
        sleep(polling_interval)
    else:
        for file in files:
            process_file_job(join(source_path,file), config)

def create_rotating_log(log_config, enable_console_logging):
    global logger

    logfilename = get_config_value_with_default(log_config, 'trace_file', 'SSFilePoller.log')
    tracepath, filename = split(logfilename)
    if not tracepath:
        tracepath = dirname(__file__)
        tracepath = join(tracepath, 'Trace')
        try:
            stat(tracepath)
        except:
            mkdir(tracepath)
        logfilename = join(tracepath, filename)

    logger = logging.getLogger("SSFilePollerRotatingLog")
    logger.setLevel(logging.DEBUG)

    file_handler = MyRotatingFileHandler(logfilename,
                                         'w',
                                         int(get_config_value_with_default(log_config, 'max_log_size', '20000000')),
                                         int(get_config_value_with_default(log_config, 'max_backup_count', '5')),
                                         'utf-8')
    formatter = logging.Formatter(get_config_value_with_default(log_config,
                                                                'log_format',
                                                                '%(asctime)s - %(levelname)s - %(message)s'))
    file_handler.setFormatter(formatter)
    if enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.info('<<<<<<<<< <<<<<<<< LOG START >>>>>>>>> >>>>>>>>')

def is_file_writable(filepath):
    try:
        f = open(filepath, 'ab')
        f.close()
        return True
    except :
        return False

def remove_file(file_to_remove):
    logger.info('Deleting file: "%s"', file_to_remove)
    if is_file_writable(file_to_remove):
        try:
            remove(file_to_remove)
        except:
            logger.info('Could not delete file: "%s"', file_to_remove)
    else :
        logger.info('Cannot delete file: "%s",file is not writable, or does not exist', file_to_remove)
