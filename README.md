**XM SendSecure** is a collaborative file exchange platform that is both highly secure and simple to use.
It is expressly designed to allow for the secured exchange of sensitive documents via virtual SafeBoxes.

# sendsecure-filepoller

**This module enables a Windows service (SendSecure File Poller) that monitors specific folders for files to be sent through the SendSecure service.**

*Note: This module has been developed using the [sendsecure-python](https://github.com/xmedius/sendsecure-python) library.*

# Table of Contents

* [Installation](#installation)
* [Quick Start](#quickstart)
* [Usage](#usage)
* [License](#license)
* [Credits](#credits)

<a name="installation"></a>
# Installation

## Prerequisites

- Python version 3.7
- Pip updated to its latest version:
  ```
  python.exe -m pip install --upgrade pip
  ```
- [pywin32](https://github.com/mhammond/pywin32) for installed Python
    ```
    pip install pywin32
    ```
- The SendSecure service, provided by [XMedius](https://www.xmedius.com/en/products?source=sendsecure-filepoller) (demo accounts available on demand)

## Install Package

Run the following command as an administrator:

```
pip install https://github.com/xmedius/sendsecure-filepoller/tarball/master --process-dependency-links
```

<a name="quickstart"></a>
# Quick Start

To enable the SendSecure File Poller service:

1. Get an Access Token with "Manage SendSecure" permission for your SendSecure enterprise account.
2. Edit the file "$PYTHON_HOME\Lib\site-packages\sendsecurefilepoller\config.ini" and change the following values:
   * ```source_path```: the path of the folder to be polled by the service.
   * ```enterprise_account```: your SendSecure enterprise account (unique identifier).
   * ```api_token```: the Access Token.
   * ```polling_interval```: the polling interval (in seconds)
3. Start the **SendSecure File Poller** service.

**Important:** Save the config file using UTF-8 encoding, the presence of a BOM will lead to an error.

<a name="usage"></a>
# Usage

To send files through a SafeBox using the SendSecure File Poller service:

1. Create a control file in json format with all properties that will be used to create the SafeBox, for example:
```json
{
    "safebox": {
        "user_email": "darthvader@empire.com",
        "subject": "Family matters",
        "message": "Son, you will find attached the evidence.",
        "security_profile_name": "Sith Security Level",
        "participants": [{
            "first_name": "",
            "last_name": "",
            "email": "lukeskywalker@rebels.com",
            "guest_options": {
              "company_name": "",
              "contact_methods": [{
                "destination": "555-232-5334",
                "destination_type": "cell"
              }]
            }
        }],
        "attachments": [{
            "file_path": "Birth_Certificate.pdf",
            "content_type": "application/pdf"
        }]
    }
}
```
**Important:** ensure to save this control file using UTF-8 encoding.

2. Drop the file(s) to attach to the SafeBox in the location(s) specified in the control file.
3. Drop the control file in the folder monitored by the SendSecure File Poller service (as specified in config.ini).

*Note: In this example, the attachment needs to be dropped in the same folder as the control file.*

<a name="license"></a>
# License

sendsecure-filepoller is distributed under [MIT License](https://github.com/xmedius/sendsecure-filepoller/blob/master/LICENSE).

<a name="credits"></a>
# Credits

sendsecure-filepoller is developed, maintained and supported by [XMedius Solutions Inc.](https://www.xmedius.com?source=sendsecure-filepoller)
The names and logos for sendsecure-filepoller are trademarks of XMedius Solutions Inc.

![XMedius Logo](https://s3.amazonaws.com/xmc-public/images/xmedius-site-logo.png)
