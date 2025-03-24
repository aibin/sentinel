# Sentinel

## Overview

Sentinel is a Django-based OpenID Connect (OIDC) provider designed to offer secure authentication and authorization services. It serves as a centralized identity management system that allows organizations to authenticate users across multiple applications using standardized protocols.

With its multi-tenant architecture, Sentinel enables multiple organizations to each have their own branded authentication experience, while sharing the same infrastructure. It supports various authentication methods including username/password, social logins (Google, Microsoft), and can be extended for custom authentication providers.

## Features

- Complete OpenID Connect (OIDC) protocol implementation
- Multi-tenant architecture with organization-based separation
- Social authentication integration (Google, Microsoft)
- Customizable user consent screens
- JWT-based tokens with RSA or HMAC signatures
- User management APIs
- Brute force protection
- Email verification and password reset workflows

## Documentation

Comprehensive documentation is available to help you get started with Sentinel:

- [General Documentation](DOCUMENTATION.md) - Complete guide to Sentinel
- [Integration Guide](INTEGRATION_GUIDE.md) - Guide for application developers integrating with Sentinel
- [Administrator Guide](ADMIN_GUIDE.md) - Guide for administrators setting up and managing Sentinel

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please refer to the documentation or open an issue on the GitHub repository.