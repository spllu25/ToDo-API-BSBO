function showRegister() {
    document.getElementById("loginBlock").style.display = "none";
    document.getElementById("registerBlock").style.display = "block";
}

function showLogin() {
    document.getElementById("registerBlock").style.display = "none";
    document.getElementById("loginBlock").style.display = "block";
}

// ---------- LOGIN ----------
async function login() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
        alert("Введите email и пароль");
        return;
    }

    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const res = await fetch("/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: form
    });

    if (!res.ok) {
        alert("Неверный email или пароль");
        return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);

    window.location.href = "/tasks-page";
}

// ---------- REGISTER ----------
async function register() {
    const nickname = document.getElementById("reg-nickname").value;
    const email = document.getElementById("reg-email").value;
    const password = document.getElementById("reg-password").value;

    if (!nickname || !email || !password) {
        alert("Заполните все поля");
        return;
    }

    const res = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nickname,
            email,
            password
        })
    });

    if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Ошибка регистрации");
        return;
    }

    alert("Регистрация успешна! Войдите.");
    showLogin();
}
