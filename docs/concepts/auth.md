# Authentication

This guide helps you learn how to login and logout using the MedPerf client to access the main production MedPerf server. MedPerf uses [passwordless authentication](https://en.wikipedia.org/wiki/Passwordless_authentication). This means that login will only require you to access your email in order complete the login process.

## Login

Follow the steps below to login:

- **Step1** Run the following command:

```bash
medperf auth login
```

You will be prompted to enter your email address.

After entering your email address, you will be provided with a verification URL and a code. A text similar to the following will be printed in your terminal:

![login_terminal](../assets/auth/login_terminal.png)

!!! tip
    If you are running the MedPerf client on a machine with no graphical interface, you can use the link on any other device, e.g. your cellphone. **Make sure that you trust that device**.

- **Step2** Open the verification URL and confirm the code:

Open the printed URL in your browser. You will be presented with a code and you will be asked to confirm if that code is the same one printed in your terminal.

![Code Confirmation](../assets/auth/code_confirmation.png)

- **Step3** After confirmation, you will be asked to enter your email address. Enter your email address and press "Continue". You will see the following screen:

![Login code](../assets/auth/login_code.png)

- **Step4** Check your inbox. You should recieve an email similar to the following:

![Login email](../assets/auth/login_email.png)

Enter the recieved code in the previous screen.

- **Step5** If there is no problem with your account, the login will be successful and you will see a screen similar to the following:

![Login success](../assets/auth/login_success.png)

## Logout

To disconnect the MedPerf client, simply run the following command:

```bash
medperf auth logout
```

## Checking the authentication status

Note that when you login, the MedPerf client will remember you as long as you are using the same `profile`. If you switch to another profile by running `medperf profile activate <other-profile>`, you may have to login again. If you switch back again to a profile where you previously logged in, your login state will be restored. Read more about profiles [here](profiles.md).

You can always check the current login status by the running the following command:

```bash
medperf auth status
```
