import sys
import logging
import os
from os.path import dirname, split

def install_service(argv):
    from .servicehelpers import handle_command_line
    new_argv = [dirname(__file__)]
    for arg in argv:
        new_argv.append(arg)
    handle_command_line(new_argv)


if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
    from servicehelpers import XMSSServiceRunner, handle_command_line
    from utils import get_config, process_jobs_in_folder, process_file_job, create_rotating_log

    if len(sys.argv) == 2 and sys.argv[1].lower() == '--poll':
        """
        Console mode polls a folder for SendSecure file jobs
        """
        create_rotating_log(get_config('logging'), True)
        logger = logging.getLogger("SSFilePollerRotatingLog")
        try:
            logger.info('Running in console mode')
            while True:
                process_jobs_in_folder(get_config('settings'))
        except KeyboardInterrupt as e:
            logger.info('<<<<<<<<< <<<<<<<< LOG STOP >>>>>>>>> >>>>>>>>>')
        except Exception as e:
            logger.error(str(e))

    elif len(sys.argv) == 3 and sys.argv[1].lower() == '--file':
        """
        One-Off mode processes the provided file job only
        """
        create_rotating_log(get_config('logging'), True)
        logger = logging.getLogger("SSFilePollerRotatingLog")
        try:
            logger.info('Running in One-Off mode')
            process_file_job(sys.argv[2], get_config('settings'))
            logger.info('<<<<<<<<< <<<<<<<< LOG STOP >>>>>>>>> >>>>>>>>>')
        except Exception as e:
            logger.error(str(e))

    else:
        """
        Handle command line for Windows service management
        """
        try:
            handle_command_line(sys.argv)
        except SystemExit as e:
            print('')
            print('Usage for console mode: \'' + split(sys.argv[0])[1] + ' --poll|--file [...]\'')
            print('Options for console mode:')
            print(' --poll : starts module for polling for SendSecure file jobs in a folder. (CTRL-C to stop)')
            print(' --file filename : One-Off mode. The file poller will process the provided file job only.')
            raise

