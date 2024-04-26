************************
Code directory structure
************************

.. code-block:: raw

    taleem-platform
    ├── manage.py
    ├── lms_gunicorn.py
    ├── cms_gunicorn.py
    ├── setup.py
    ├── package.json
    ├── webpack.common.config.js
    ├── webpack.dev.config.js
    ├── webpack.prod.config.js
    ├── requirements
    │    └── edx
    │       └── base.txt
    ├── lms
    │   ├── djangoapps
    │   ├── static
    │   └── templates
    ├── cms
    │   ├── djangoapps
    │   ├── static
    │   └── templates
    ├── common
    │   ├── djangoapps
    │   ├── static
    │   └── templates
    ├── openedx
    │   ├── core
    │   │   └── djangoapps
    │   │       ├── app1
    │   │       └── app2
    │   ├── features
    │   │   ├── app1
    │   │   └── app2
    │   └── custom
    │       ├── app1
    │       └── app2
    └── themes
        └── taleem-theme
            ├── lms
            │   ├── static
            │   └── templates
            └── cms
                ├── static
                └── templates


lms
---
Code related to Learning Management System

cms
---
Code related to Content Management System

common
------
Code shared between lms and cms

openedx
-------
This is the root package for Open edX. The intent is that all importable code
from Open edX will eventually live here, including the code in the lms, cms,
and common directories.

Node JS packages
----------------
To change the version or any existing package or to add new dependencies modify **package.json**

Where we put most of the custom Django apps?
--------------------------------------------

.. code-block:: raw

    ├── openedx
    │   └── custom
    │       ├── app1
    │       └── app2

Where we put front end files?
-----------------------------

.. code-block:: raw

    └── themes
        └── taleem-theme
            ├── lms
            │   ├── static
            │   └── templates
            └── cms
                ├── static
                └── templates

Adding custom Django apps
-------------------------
1. Put your custom app to **openedx/custom/your_app_dir**
2. Register app name to **lms/envs/common.py** or
   **cms/envs/common.py** under **TALEEM_APPS** list
   (You may register same app at both lms and cms)
3. Add URL patterns to **lms/urls.py** or **cms/urls.py**
4. Add views.py to your Django app to handle URL endpoints
5. Add HTML (mako template) to **themes/lms/templates/your_app_name/**
6. You may define database tables to your_app/models.py
7. You may define admin panel to your_app/admin.py


Adding custom REST APIs
-----------------------
1. Create a directory named as **api** to your custom app
2. Add urls.py, views.py etc. files to your custom app
3. Register urls.py to lms/urls.py or cms/urls.py as follows:
   url(r'^api/your-app-slug/', include('openedx.custom.your_app.api.urls')),


How to include pip packages?
----------------------------
Include extra pip packages to requirements/edx/base.txt

Register pip package to lms/envs/common.py or cms/envs/common.py
under **COMMUNITY_APPS** list

If the external package requires to add new settings then
you may add to lms/envs/common.py or cms/envs/common.py

Modify existing apps
--------------------
Currently we are allowing to change the core openedx code in lms, common, cms and openedx directories.

To override the front-end files, use themes as follows:

1. Copy the template from core code (for example: lms/templates/index.html)
2. Put it at themes/taleem-theme/lms/templates/index.html
3. Modify as you want


Build Docker image
------------------
We have build pipeline which uses .drone.yaml file.
Build pipeline triggers on master branch commit/PR merge events.
You may view the builds at `<https://drone.creativeadvtech.ml/creativeadvtech/taleem-platform/>`_

It is possible to deploy the build on staging from the drone web interface.

1. Go to `drone URL <https://drone.creativeadvtech.ml/creativeadvtech/taleem-platform/>`_
2. Select the build
3. Click promote
4. Enter env as **staging**


OpenedX version and devstack
----------------------------
We are using **Juniper** version of openedx as base code.
For local development we are using `devstack <https://github.com/openedx/devstack>`_

