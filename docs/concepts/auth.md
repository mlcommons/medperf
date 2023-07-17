# Authentication and Account Management

## Login

Run the following command to login:

```bash
medperf auth login
```

You will be provided with a verification URL and a code, similar to the following:

```bash
Please go to the following link to complete your login request:
        https://dev-5xl8y6uuc2hig2ly.us.auth0.com/activate?user_code=TFCX-CRZP

Ensure that you will be presented with the following code:
        TFCX-CRZP
```

In order to complete the login process, open the link in your browser. You will be presented with a code and you will be asked to confirm if that code resembles the one provided previously through the command line interface.

After confirmation, you will be asked to enter your credentials.

## Logout

To logout, simply run the following command:

```bash
medperf auth logout
```

## Change your Password

In case you want to change your account password, run the following command:

```bash
medperf auth change_password
```

You will be asked to provide your email address. Once you provide your email address, a verification link will be sent to your email. To change your password, simply open your inbox, click on the provided link, and follow the instructions.
