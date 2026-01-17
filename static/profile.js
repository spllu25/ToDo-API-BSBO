const token = localStorage.getItem("token");

if (!token) window.location.href = "/";

async function loadProfile() {
    const res = await fetch("/users/me", {
        headers: { "Authorization": "Bearer " + token }
    });

    const user = await res.json();

    document.getElementById("nickname").value = user.nickname;
    document.getElementById("email").value = user.email;
}

async function updateProfile() {
    const nickname = document.getElementById("nickname").value;
    const password = document.getElementById("password").value;

    const body = {};
    if (nickname) body.nickname = nickname;
    if (password) body.password = password;

    const res = await fetch("/users/me", {
        method: "PUT",
        headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    if (!res.ok) {
        alert("Ошибка обновления профиля");
        return;
    }

    alert("Профиль обновлён");
    document.getElementById("password").value = "";
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}

loadProfile();
