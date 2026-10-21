# EcoCoin — Smart Waste Reward System

A Python-only hackathon prototype built with Streamlit, SQLite, Pandas, and Matplotlib.

## Features

- User registration and sign-in
- Persistent SQLite database
- Waste submission and eligibility validation
- Configurable illustrative reward rates
- Admin approval/rejection workflow
- Wallet transactions credited once per approved request
- Collection point directory and admin management
- User and platform dashboards with charts
- Unit tests for reward rules

## Requirements

- Python 3.10 or newer recommended
- Internet connection for initial package installation only

## Windows setup

Open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Then run the install, test, and launch commands shown above.

## Demo administrator

- Username: `admin`
- Password: `EcoCoinDemo2026!`

This is a known demo credential. Use only for a local demo, change it before any real deployment, and do not expose this prototype to the public internet as-is. The app hashes stored passwords, but production deployment needs stronger account-management and secret-configuration practices.

## Demo walkthrough

1. Create a regular user account.
2. Sign in as that user.
3. Submit 2 kg of Plastic to a collection point that accepts Plastic.
4. Confirm the request is Pending and estimates 20 EcoCoins.
5. Sign out and sign in as `admin`.
6. Open Review requests and approve the request.
7. Sign back in as the user and open the wallet.
8. Confirm the balance is 20 EcoCoins and the impact dashboard counts the approved 2 kg.
9. Try to approve the same request again; the app must refuse because the request is no longer Pending.

## Reward rules

Initial demonstration rates:
- Plastic: 10 EcoCoins/kg
- Polythene: 8 EcoCoins/kg
- Rubber: 6 EcoCoins/kg
- Wood: 4 EcoCoins/kg

Automobile waste and construction waste are initially ineligible. The administrator can change category eligibility and rates. Fractional rewards are rounded down to whole EcoCoins. For example, 1.29 kg of plastic earns 12 EcoCoins if approved.

A request does not earn points while pending or after rejection. The request status update and wallet transaction are written in one SQLite transaction. A unique constraint on `transactions.request_id` prevents multiple credits for one request.

## Demo collection points

Starter points are fictional demonstration records. They are not verified real collection centers. An administrator can add actual points after verifying their address, operating hours, contact information, and accepted waste types.

## Project structure

```text
ecocoin/
├── app.py
├── auth.py
├── config.py
├── database.py
├── rewards.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
└── tests/
    └── test_rewards.py
```

## Testing

```powershell
python -m unittest discover -s tests -v
```

The tests cover reward calculation, invalid quantities, rejected categories, collection-point compatibility, and valid submissions.

## Known prototype limitations

- Authentication is intended for a local hackathon demo, not public production deployment.
- The default admin credential is public and must be changed before any real use.
- Collection points and reward rates are illustrative until verified by a real operator.
- Waste submissions are user-reported; the prototype does not independently verify physical weight or recycling.
- No carbon-saving estimate is shown because that would require defensible factors and assumptions.
- For real multi-user deployment, add robust account recovery, rate limiting, secure secret management, audit logs, deployment hardening, and a physical verification workflow.

## GitHub upload (Windows PowerShell)

1. Create a new **empty** repository on https://github.com/new. Do not add a README there if this folder already has one.
2. Open VS Code Terminal in the folder containing `app.py` and `requirements.txt`.
3. Run these commands, replacing the URL with your own repository URL:

```powershell
git init
git add .
git status
git commit -m "Build EcoCoin glass UI"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If Git says your identity is unknown, configure it once with your own details:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

If `git` is not recognized, install Git for Windows from https://git-scm.com/download/win, restart VS Code, and retry. If `origin` already exists, run `git remote -v` and use `git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git` instead of adding it again.

### Upload through the GitHub website (no Git commands)

1. Create a new repository at https://github.com/new.
2. Open the repository and choose **Add file → Upload files**.
3. Drag the project files and folders from your extracted `ecocoin` folder into the browser. Upload the contents of the project folder, including `app.py`, `database.py`, `requirements.txt`, `auth.py`, `config.py`, `rewards.py`, `README.md`, `.gitignore`, `.streamlit/config.toml`, and `tests/`.
4. Do not upload `.venv`, Python cache folders, local database files, `.env`, or `.streamlit/secrets.toml`.
5. Enter a commit message and select **Commit changes**.

## Public demo deployment with Streamlit Community Cloud

1. Push the project to GitHub using the instructions above.
2. Visit https://share.streamlit.io/ and sign in with GitHub.
3. Select **Create app**, choose your repository and `main` branch, and set the app file path to `app.py`.
4. Select **Deploy** and wait for the public app URL.

**Before sharing publicly:** this is a hackathon prototype. The demo administrator account is created automatically with a known password; do not expose this app publicly as-is. Remove/change the demo admin setup and create a secure administrator provisioning method first. The starter collection points are fictional. SQLite stored on a cloud app's local filesystem may not be durable or suitable for concurrent public use; use a managed persistent database such as PostgreSQL for a real multi-user launch. Never commit secrets, credentials, or real user data to GitHub.

## Separate wallets

Each account has its own numeric user ID. Waste requests and wallet transactions are stored with that `user_id`, and wallet balance/history queries filter by the signed-in user's ID. As a result, a normal user sees only their own wallet and requests; the administrator can review platform-wide records. For a public production service, retain these ownership checks and add security testing before launch.
