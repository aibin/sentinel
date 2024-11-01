# Sentinel

## Overview

Sentinel is a Django-based OpenID Connect (OIDC) provider designed to offer secure authentication and authorization services. It includes a set of management commands to set up and maintain the OIDC provider.

## Features

- Django-based implementation
- OpenID Connect (OIDC) support
- Management commands for easy setup and maintenance

## Getting Started

To get started with Sentinel, follow these steps:

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/sentinel.git
    cd sentinel
    ```

2. Install the required dependencies:
    ```sh
    pipenv install
    ```

3. Apply the database migrations:
    ```sh
    ./manage.py migrate
    ```

4. Create the necessary keys and tokens:
    ```sh
    ./manage.py creatersakey
    ./manage.py createorganization
    ./manage.py createresponsetypes
    ./manage.py createmgmttoken
    ./manage.py createsuperuser
    ./manage.py creategroups
    ```

5. Start the development server:
    ```sh
    ./manage.py runserver
    ```

## Running in Staging

To run Sentinel in a staging environment, use Honcho with the provided `honcho.ini` file:
```sh
honcho start -f honcho.ini
```