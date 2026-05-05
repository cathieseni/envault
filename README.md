# envault

> Lightweight .env file manager with per-project secret rotation and audit logs.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envault
```

---

## Usage

**Initialize a project vault:**

```bash
envault init
```

**Add or update a secret:**

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/db"
```

**Rotate a secret and log the change:**

```bash
envault rotate DATABASE_URL "postgres://user:newpass@localhost/db"
```

**Export secrets to a `.env` file:**

```bash
envault export > .env
```

**View the audit log:**

```bash
envault log
# 2024-06-01 12:00:01  SET       DATABASE_URL
# 2024-06-01 14:32:10  ROTATE    DATABASE_URL
```

Secrets are stored per-project and never leave your local environment unless explicitly exported.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## License

[MIT](LICENSE)