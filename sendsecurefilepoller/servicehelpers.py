import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import logging
from utils import process_jobs_in_folder, get_config, create_rotating_log

class XMSSServiceRunner (win32serviceutil.ServiceFramework):
    _svc_name_ = "sendsecurefilepoller"
    _svc_display_name_ = "SendSecure File Poller"
    _svc_description_ = "Monitors specific folders for files to be sent through the SendSecure service"
    IsStopping = False

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.IsStopping = True
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        logger = logging.getLogger("SSFilePollerRotatingLog")
        logger.info('<<<<<<<<< <<<<<<<< LOG STOP >>>>>>>>> >>>>>>>>>')

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()

    def main(self):
        try:
            create_rotating_log(get_config('logging'), False)
            logger = logging.getLogger("SSFilePollerRotatingLog")
            logger.info('Running in service mode')

            while not self.IsStopping:
                process_jobs_in_folder(get_config('settings'))
        except Exception, e:
            logger.error(str(e))

def handle_command_line(argv):
    return win32serviceutil.HandleCommandLine(XMSSServiceRunner, None, argv)

