
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    user_options = install.user_options + [
        ('noservice', None, None),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.noservice = None

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        install.run(self)
        if not self.noservice:
            from sendsecurefilepoller import sendsecurefilepoller
            sendsecurefilepoller.install_service(['--startup', 'auto', 'install'])

setup(
    name='sendsecurefilepoller',
    version='1.0.0',
    description='The Python module to be used to create XMediusSENDSECURE safebox from control file jobs',
    long_description='See https://github.com/xmedius/sendsecure-filepoller for more information',
    url='https://github.com/xmedius/sendsecure-filepoller/',
    author='XMedius R&D',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Environment :: Win32 (MS Windows)',
        'Operating System :: Microsoft :: Windows'
    ],
    cmdclass={
        'install': PostInstallCommand
    },
    packages=['sendsecurefilepoller'],
    package_data={'sendsecurefilepoller': ['config.ini']},
    install_requires=['sendsecure'],
    dependency_links=['https://github.com/xmedius/sendsecure-python/tarball/master/#egg=sendsecure-0']
)
